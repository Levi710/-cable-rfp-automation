import requests
from typing import List, Dict
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class GeMAIECrawler:
    """
    GeM crawler with fallback strategies:
    1. Try public API
    2. Fallback to web scraping
    3. Use RSS feeds if available
    """
    
    def __init__(self):
        self.base_url = "https://gem.gov.in"
        self.api_base = "https://gem.gov.in/api/v1"
        self.cable_categories = ["20005", "20006", "20007", "20008"]
    
    def search_cable_tenders(self, days_remaining: int = 90) -> List[Dict]:
        """Search with multiple strategies."""
        
        # Strategy 1: Try public search page (web scraping)
        tenders = self._scrape_public_search()
        
        if tenders:
            logger.info(f"✅ GeM web scraping: Found {len(tenders)} tenders")
            return tenders
        
        # Strategy 2: Try RSS feed (if available)
        tenders = self._check_rss_feed()
        
        if tenders:
            logger.info(f"✅ GeM RSS: Found {len(tenders)} tenders")
            return tenders
        
        logger.warning("⚠️ GeM: All strategies failed")
        return []
    
    def _scrape_public_search(self) -> List[Dict]:
        """
        Scrape GeM public tender search page.
        No authentication needed.
        """
        
        try:
            # GeM public search URL
            search_url = f"{self.base_url}/search/tenders"
            
            response = requests.get(
                search_url,
                params={
                    'q': 'cable wire electrical',
                    'status': 'active'
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"GeM search returned {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tenders = []
            
            # Find tender cards/items
            tender_items = soup.find_all('div', class_=['tender-card', 'bid-card', 'tender-item'])
            
            for item in tender_items:
                try:
                    tender = self._parse_tender_item(item)
                    if tender and self._is_cable_tender(tender):
                        tenders.append(tender)
                except Exception as e:
                    logger.debug(f"Error parsing item: {str(e)}")
            
            return tenders
        
        except Exception as e:
            logger.error(f"GeM scraping error: {str(e)}")
            return []
    
    def _parse_tender_item(self, item) -> Dict:
        """Parse tender item from HTML."""
        
        title_elem = item.find(['h3', 'h4', 'h5', 'a'])
        
        return {
            'source': 'GeM Portal',
            'tender_id': f"GEM-{item.get('data-id', 'unknown')}",
            'title': title_elem.text.strip() if title_elem else '',
            'description': item.get_text()[:500],
            'organization': item.find('span', class_='org-name').text.strip() if item.find('span', class_='org-name') else 'Unknown',
            'url': f"{self.base_url}{title_elem['href']}" if title_elem and title_elem.get('href') else '',
            'raw_data': item.get_text()
        }
    
    def _check_rss_feed(self) -> List[Dict]:
        """Check GeM RSS feed if available."""
        
        try:
            rss_url = f"{self.base_url}/rss/tenders"
            
            response = requests.get(rss_url, timeout=10)
            
            if response.status_code == 200:
                # Parse RSS XML
                root = ET.fromstring(response.content)
                
                tenders = []
                for item in root.findall('.//item'):
                    title = item.find('title').text if item.find('title') is not None else ''
                    
                    if self._has_cable_keywords(title):
                        tenders.append({
                            'source': 'GeM RSS',
                            'title': title,
                            'description': item.find('description').text if item.find('description') is not None else '',
                            'url': item.find('link').text if item.find('link') is not None else ''
                        })
                
                return tenders
        
        except Exception as e:
            logger.debug(f"RSS feed not available: {str(e)}")
        
        return []
    
    def _is_cable_tender(self, tender: dict) -> bool:
        """Check if tender is cable-related."""
        
        cable_keywords = ['cable', 'wire', 'conductor', 'xlpe', 'pvc', 'transmission', 'distribution', 'power cable', 'armored']
        text = (tender.get('title', '') + ' ' + tender.get('description', '')).lower()
        
        return any(keyword in text for keyword in cable_keywords)
    
    def _has_cable_keywords(self, text: str) -> bool:
        """Quick check for cable keywords."""
        
        text = text.lower()
        return any(kw in text for kw in ['cable', 'wire', 'conductor', 'xlpe', 'pvc'])
