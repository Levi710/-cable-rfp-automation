try:
    import requests
except Exception:  # pragma: no cover
    requests = None
import logging
import json
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class BharatTenderCrawler:
    """
    BharatTender crawler with demo fallback when API is unreachable.
    """
    
    def __init__(self):
        self.base_url = "https://bharattender.gov.in/api"  # Placeholder
    
    def _load_demo(self) -> List[Dict]:
        try:
            demo_path = Path(__file__).resolve().parent.parent / 'data' / 'feeds' / 'bharat_demo.json'
            with open(demo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tenders = data.get('tenders', [])
            logger.info(f"BharatTender Demo: Loaded {len(tenders)} demo tenders")
            return tenders
        except Exception as e:
            logger.warning(f"BharatTender Demo fallback failed: {e}")
            return []
    
    def search_tenders(self) -> List[Dict]:
        """
        Try official API; fallback to local demo data.
        """
        
        if not requests:
            logger.info("BharatTender: 'requests' not available in environment. Using demo tenders.")
            return self._load_demo()
        try:
            response = requests.get(
                f"{self.base_url}/tenders/search",
                params={
                    'keywords': 'cable,electrical,power',
                    'status': 'active',
                    'sector': 'electrical',
                    'pagesize': 100
                },
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'CableRFPBot/1.0'
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                tenders = data.get('results', [])
                logger.info(f"BharatTender: {len(tenders)} tenders found")
                formatted = []
                for tender in tenders:
                    formatted.append({
                        'source': 'BharatTender (Official)',
                        'tender_id': tender.get('tender_id', f"BT-{hash(str(tender)) % 100000}"),
                        'title': tender.get('description', tender.get('title', 'Unknown')),
                        'organization': tender.get('procuring_entity', 'Unknown'),
                        'deadline': tender.get('bid_closing_date'),
                        'estimated_value': tender.get('estimated_tender_value', 0),
                        'location': tender.get('state'),
                        'url': f"https://bharattender.gov.in/tender/{tender.get('tender_id')}",
                        'description': tender.get('description', ''),
                        'raw_data': tender
                    })
                return formatted
            else:
                logger.warning(f"BharatTender returned status {response.status_code}. Falling back to demo.")
                return self._load_demo()
        except Exception as e:
            logger.error(f"BharatTender error: {str(e)}. Falling back to demo.")
            return self._load_demo()
