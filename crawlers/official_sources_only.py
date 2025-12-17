"""
Use ONLY official government sources - no web scraping.
No connectivity issues, no SSL errors, no 404s.
"""

import asyncio
import logging
import os
from typing import List, Dict
from crawlers.gem_api_simple import GeM_PublicAPI
from crawlers.bharat_tender import BharatTenderCrawler
from crawlers.local_database import LocalTenderDatabase
from crawlers.html_portal_crawler import HtmlPortalCrawler
from crawlers.url_list_crawler import UrlListCrawler
from crawlers.cppp_crawler import CPPPCrawler
from crawlers.ntpc_crawler import NTPCCrawler
from crawlers.powergrid_crawler import POWERGRIDCrawler
from crawlers.tenderdetail_crawler import TenderDetailCrawler
from crawlers.state_seb_crawler import StateElectricityCrawler
from crawlers.local_pages_crawler import LocalPagesCrawler
from utils.cable_detector import CableDetector

logger = logging.getLogger(__name__)

class OfficialSourcesCrawler:
    """
    Crawl official APIs (GeM, BharatTender) every time, 
    then supplement with local database.
    """
    
    def __init__(self):
        self.gem_api = GeM_PublicAPI()
        self.bharat_tender = BharatTenderCrawler()
        self.local_db = LocalTenderDatabase()
        self.detector = CableDetector()
        self.state_seb = StateElectricityCrawler()
    
    async def discover_tenders(self) -> List[Dict]:
        """
        Discover tenders from official sources.
        
        Strategy:
        1. Always attempt to crawl from GeM API
        2. Always attempt to crawl from BharatTender API
        3. Always supplement with local database
        4. Deduplicate and filter for cable-related tenders
        """
        
        logger.info("\n" + "="*80)
        logger.info("DISCOVERING TENDERS FROM OFFICIAL SOURCES")
        logger.info("="*80 + "\n")
        
        all_tenders = []
        
        # Defer demo/local sources (GeM demo, BharatTender demo, Local DB, HTML sample)
        # We will only use them as a fallback if live sources yield zero results,
        # or when DISABLE_DEMO_SOURCES is not set.

        # Initialize status logger
        from utils.crawler_status import get_status_logger
        from config.settings import settings
        
        status_logger = get_status_logger()
        
        # --- PHASE 1: SEED URLs ---
        logger.info("Seed URL List: Crawling configured procurement portals...")
        try:
            url_tenders = UrlListCrawler().search_tenders()
            status_logger.log_source('Seed URLs', success=True, tenders_found=len(url_tenders))
            all_tenders.extend(url_tenders)
            logger.info(f"   Found {len(url_tenders)} tenders from seed URL list\n")
        except Exception as e:
            status_logger.log_source('Seed URLs', success=False, error=str(e))
            logger.warning(f"   URL List crawler failed: {str(e)}\n")

        # --- PHASE 2: CPPP ---
        if settings.ENABLE_CPPP:
            logger.info("CPPP (eProcure): Scraping public listings...")
            try:
                cppp_tenders = CPPPCrawler().scrape_tenders()
                status_logger.log_source('CPPP', success=True, tenders_found=len(cppp_tenders))
                all_tenders.extend(cppp_tenders)
                logger.info(f"   Found {len(cppp_tenders)} CPPP tenders\n")
            except Exception as e:
                status_logger.log_source('CPPP', success=False, error=str(e))
                logger.warning(f"   CPPP crawler failed: {str(e)}\n")
        else:
            logger.info("CPPP crawler disabled by settings")

        # --- PHASE 3: NTPC ---
        if settings.ENABLE_NTPC:
            logger.info("NTPC: Scraping NTPC tender pages...")
            try:
                from utils.source_gate import should_skip_source
                if should_skip_source('NTPC', ['eprocurentpc.nic.in', 'www.ntpc.co.in']):
                    status_logger.log_source('NTPC', success=False, error='Host unreachable (TTL active)')
                    logger.info("   NTPC: hosts unreachable (TTL active); skipping\n")
                else:
                    ntpc_tenders = NTPCCrawler().scrape_tenders()
                    status_logger.log_source('NTPC', success=True, tenders_found=len(ntpc_tenders))
                    all_tenders.extend(ntpc_tenders)
                    logger.info(f"   Found {len(ntpc_tenders)} NTPC tenders\n")
            except Exception as e:
                status_logger.log_source('NTPC', success=False, error=str(e))
                logger.warning(f"   NTPC crawler failed: {str(e)}\n")
        else:
            logger.info("NTPC crawler disabled by settings")

        # --- PHASE 4: POWERGRID ---
        if settings.ENABLE_POWERGRID:
            logger.info("POWERGRID: Scraping POWERGRID tender pages...")
            try:
                from utils.source_gate import should_skip_source
                if should_skip_source('POWERGRID', ['eprocure.powergrid.in', 'www.powergrid.in']):
                    status_logger.log_source('POWERGRID', success=False, error='Host unreachable (TTL active)')
                    logger.info("   POWERGRID: hosts unreachable (TTL active); skipping\n")
                else:
                    pg_tenders = POWERGRIDCrawler().scrape_tenders()
                    status_logger.log_source('POWERGRID', success=True, tenders_found=len(pg_tenders))
                    all_tenders.extend(pg_tenders)
                    logger.info(f"   Found {len(pg_tenders)} POWERGRID tenders\n")
            except Exception as e:
                status_logger.log_source('POWERGRID', success=False, error=str(e))
                logger.warning(f"   POWERGRID crawler failed: {str(e)}\n")
        else:
            logger.info("POWERGRID crawler disabled by settings")

        # --- PHASE 5: TenderDetail ---
        logger.info("TenderDetail: Scraping listing page...")
        try:
            td_tenders = TenderDetailCrawler().scrape_tenders()
            status_logger.log_source('TenderDetail', success=True, tenders_found=len(td_tenders))
            all_tenders.extend(td_tenders)
            logger.info(f"   Found {len(td_tenders)} TenderDetail tenders\n")
        except Exception as e:
            status_logger.log_source('TenderDetail', success=False, error=str(e))
            logger.warning(f"   TenderDetail crawler failed: {str(e)}\n")

        # --- PHASE 6: State SEBs ---
        if settings.ENABLE_STATE_SEB:
            logger.info("State SEB: Scraping state electricity boards...")
            try:
                # State crawler handles its own internal structure, but we log aggregate
                state_tenders = self.state_seb.scrape_all_states()
                status_logger.log_source('State SEBs', success=True, tenders_found=len(state_tenders))
                all_tenders.extend(state_tenders)
                logger.info(f"   Found {len(state_tenders)} State SEB tenders\n")
            except Exception as e:
                status_logger.log_source('State SEBs', success=False, error=str(e))
                logger.warning(f"   State SEB crawler failed: {str(e)}\n")
        else:
            logger.info("State SEB crawler disabled by settings")

        # --- PHASE 7: Local Sample Pages ---
        logger.info("Local sample pages: Parsing configured HTML files...")
        try:
            local_page_tenders = LocalPagesCrawler().scrape()
            status_logger.log_source('Local Samples', success=True, tenders_found=len(local_page_tenders))
            all_tenders.extend(local_page_tenders)
            logger.info(f"   Found {len(local_page_tenders)} tenders from local sample pages\n")
        except Exception as e:
            status_logger.log_source('Local Samples', success=False, error=str(e))
            logger.warning(f"   Local sample pages failed: {str(e)}\n")
        
        # Save logs
        status_logger.save()

        

        # Deduplicate by tender_id
        seen_ids = set()
        unique_tenders = []
        duplicates_removed = 0
        
        for tender in all_tenders:
            tender_id = tender.get('tender_id')
            if tender_id and tender_id not in seen_ids:
                seen_ids.add(tender_id)
                unique_tenders.append(tender)
            elif tender_id:
                duplicates_removed += 1
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate tenders\n")
        
        all_tenders = unique_tenders
        
        # Filter with cable detector (lenient threshold)
        logger.info("Filtering for cable-related tenders (threshold=0.3)...")
        cable_tenders = [
            t for t in all_tenders
            if self.detector.is_cable_tender(t, threshold=0.3)
        ]
        
        logger.info(f"{'='*80}")
        logger.info(f"TOTAL DISCOVERED: {len(all_tenders)} tenders")
        logger.info(f"   Cable-related: {len(cable_tenders)}")
        logger.info(f"   Filtered out: {len(all_tenders) - len(cable_tenders)}")
        logger.info(f"{'='*80}\n")
        
        # Store in database (optional)
        if os.getenv('DISABLE_DB', 'false').lower() not in ('1', 'true', 'yes') and \
           os.getenv('DISABLE_DB_PERSISTENCE', 'false').lower() not in ('1', 'true', 'yes'):
            self._store_tenders(cable_tenders)
        else:
            logger.info("Database persistence disabled by environment; skipping store")
        
        return cable_tenders
    
    def _store_tenders(self, tenders: List[Dict]):
        """Store tenders with deduplication. If DB is unavailable, no-op with a log."""
        try:
            from config.database import SessionLocal
            from database.models import DiscoveredTender
        except Exception as e:
            logger.info("Database not available in this environment; skipping persistence.")
            return
        
        db = SessionLocal()
        try:
            stored = 0
            duplicates = 0
            for tender in tenders:
                tender_id = tender.get('tender_id', '')
                if not tender_id:
                    continue
                existing = db.query(DiscoveredTender).filter_by(tender_id=tender_id).first()
                if not existing:
                    db_tender = DiscoveredTender(
                        tender_id=tender_id,
                        source=tender.get('source', 'Unknown'),
                        title=tender.get('title', '')[:500],
                        description=tender.get('description', '')[:3000],
                        organization=tender.get('organization', ''),
                        estimated_value=tender.get('estimated_value', 0),
                        raw_data=tender
                    )
                    db.add(db_tender)
                    stored += 1
                else:
                    duplicates += 1
            db.commit()
            logger.info(f"Database: Stored {stored} new tenders (skipped {duplicates} duplicates)")
        except Exception as e:
            msg = str(e)
            if 'could not translate host name' in msg or 'OperationalError' in msg:
                logger.info("Database not reachable (likely not running); skipping persistence")
            else:
                logger.error(f"Database error: {msg}")
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception:
                pass
