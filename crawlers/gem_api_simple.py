try:
    import requests
except Exception:  # pragma: no cover
    requests = None
import json
import logging
import os
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class GeM_PublicAPI:
    """
    GeM public API access with graceful demo fallback.
    If no API key or API fails, loads demo tenders from data/feeds/gem_demo.json.
    """
    
    def __init__(self):
        self.base_url = "https://api.data.gov.in/resource"
        self.gem_dataset_id = "5fb0cd5b8fce0db8df05e0cd"  # Placeholder dataset
        self.api_key = os.getenv('GEM_API_KEY')
    
    def _load_demo(self) -> List[Dict]:
        """Load demo tenders from local JSON file (works offline)."""
        try:
            demo_path = Path(__file__).resolve().parent.parent / 'data' / 'feeds' / 'gem_demo.json'
            with open(demo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tenders = data.get('tenders', [])
            logger.info(f"GeM Demo: Loaded {len(tenders)} demo tenders")
            return tenders
        except Exception as e:
            logger.warning(f"GeM Demo fallback failed: {e}")
            return []
    
    def search_cable_tenders(self) -> List[Dict]:
        """Search GeM; fallback to demo if no key or failure."""
        
        # No API key -> demo mode
        if not self.api_key:
            logger.info("GeM: No API key provided. Using demo tenders.")
            return self._load_demo()
        
        if not requests:
            logger.info("GeM: 'requests' not available in environment. Using demo tenders.")
            return self._load_demo()
        try:
            url = f"{self.base_url}/{self.gem_dataset_id}"
            params = {
                'api-key': self.api_key,
                'format': 'json',
                'filters[category]': 'cable',
                'filters[status]': 'open',
                'limit': 100
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                tenders = data.get('records', [])
                logger.info(f"GeM Public API: {len(tenders)} tenders found")
                formatted = []
                for tender in tenders:
                    formatted.append({
                        'source': 'GeM Public API',
                        'tender_id': tender.get('tender_id', f"GEM-{hash(str(tender)) % 100000}"),
                        'title': tender.get('tender_title', tender.get('title', 'Unknown')),
                        'organization': tender.get('buyer_organization', 'Unknown'),
                        'deadline': tender.get('last_bid_date'),
                        'estimated_value': tender.get('estimated_cost', 0),
                        'description': tender.get('description', ''),
                        'raw_data': tender
                    })
                return formatted
            else:
                logger.warning(f"GeM API returned status {response.status_code}. Falling back to demo.")
                return self._load_demo()
        except Exception as e:
            logger.error(f"GeM API error: {str(e)}. Falling back to demo.")
            return self._load_demo()
