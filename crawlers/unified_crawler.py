import asyncio
import logging
import time
from typing import List, Dict
from crawlers.gem_crawler import GeMAIECrawler
from crawlers.powergrid_crawler import POWERGRIDCrawler
from crawlers.state_seb_crawler import StateElectricityCrawler
from crawlers.ntpc_crawler import NTPCCrawler
from crawlers.adaptive_scheduler import AdaptiveScheduler
from utils.cable_detector import CableDetector
from database.models import DiscoveredTender
from config.database import SessionLocal
from database.queries import Queries
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
DISCOVERED_COUNTER = Counter(
    'tenders_discovered_total', 'Total number of tenders discovered', ['source']
)
DISCOVERY_LATENCY = Histogram(
    'tender_discovery_seconds', 'Time spent discovering tenders'
)

class UnifiedCrawler:
    """Unified crawler with improved error handling and cable detection."""
    
    def __init__(self):
        self.scheduler = AdaptiveScheduler()  # INNOVATION 1: Adaptive scheduler
        self.gem = GeMAIECrawler()
        self.powergrid = POWERGRIDCrawler()
        self.state_seb = StateElectricityCrawler()
        self.ntpc = NTPCCrawler()
        self.detector = CableDetector()  # Enhanced cable detection
    
    async def discover_all_tenders(self) -> List[Dict]:
        """Discover from all sources in parallel."""
        
        logger.info("Starting unified tender discovery...")
        start = time.time()
        
        tasks = [
            self._run_gem(),
            self._run_powergrid(),
            self._run_state_seb(),
            self._run_ntpc()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_tenders: List[Dict] = []
        for result in results:
            if isinstance(result, list):
                all_tenders.extend(result)
        
        # Re-filter with advanced detector (lowered threshold for more results)
        cable_tenders = [
            t for t in all_tenders
            if self.detector.is_cable_tender(t, threshold=0.3)  # More lenient: 0.3 instead of 0.6
        ]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ DISCOVERY COMPLETE")
        logger.info(f"   Total discovered: {len(all_tenders)}")
        logger.info(f"   Cable-related: {len(cable_tenders)}")
        logger.info(f"   Filtered out: {len(all_tenders) - len(cable_tenders)}")
        logger.info(f"{'='*80}\n")
        
        DISCOVERY_LATENCY.observe(time.time() - start)
        
        # Increment counters per source
        for t in cable_tenders:
            DISCOVERED_COUNTER.labels(source=t.get('source', 'Unknown')).inc()
        
        # Store in database via queries helper
        self._store_tenders(cable_tenders)
        
        return cable_tenders
    
    async def _run_gem(self):
        """Run GeM crawler with adaptive scheduling."""
        if self.scheduler.should_crawl_now('gem'):
            logger.info("Running GeM crawler")
            tenders = self.gem.search_cable_tenders()
            self.scheduler.record_crawl('gem', len(tenders), True, 150)
            return tenders
        return []
    
    async def _run_powergrid(self):
        """Run POWERGRID crawler with adaptive scheduling."""
        if self.scheduler.should_crawl_now('powergrid'):
            logger.info("Running POWERGRID crawler")
            tenders = self.powergrid.scrape_tenders()
            self.scheduler.record_crawl('powergrid', len(tenders), True, 2500)
            return tenders
        return []
    
    async def _run_state_seb(self):
        """Run State SEB crawler with adaptive scheduling."""
        if self.scheduler.should_crawl_now('state_seb'):
            logger.info("Running State SEB crawler")
            tenders = self.state_seb.scrape_all_states()
            self.scheduler.record_crawl('state_seb', len(tenders), True, 3000)
            return tenders
        return []
    
    async def _run_ntpc(self):
        """Run NTPC crawler with adaptive scheduling."""
        if self.scheduler.should_crawl_now('ntpc'):
            logger.info("Running NTPC crawler")
            tenders = self.ntpc.scrape_tenders()
            self.scheduler.record_crawl('ntpc', len(tenders), True, 2000)
            return tenders
        return []
    
    def _store_tenders(self, tenders: List[Dict]):
        """Store discovered tenders in database."""
        db = SessionLocal()
        try:
            Queries.upsert_tenders(db, tenders)
            logger.info(f"Upserted {len(tenders)} tenders in database")
        except Exception as e:
            logger.error(f"Error storing tenders: {str(e)}")
            db.rollback()
        finally:
            db.close()
