import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import urllib3

# Disable SSL warnings for problematic sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class StateElectricityCrawler:
    """
    State SEB crawler with robust error handling.
    """
    
    def __init__(self):
        self.state_seb_urls = {
            'maharashtra': {
                'url': 'https://mahadiscom.in/tender-notifications/',  # Updated MSEDCL tender page
                'verify_ssl': True
            },
            'uttar_pradesh': {
                'url': 'https://www.uppcl.org/tenders.aspx',
                'verify_ssl': True
            },
            'tamil_nadu': {
                'url': 'https://www.tangedco.gov.in/tenders',
                'verify_ssl': False  # SSL issues known
            },
            'karnataka': {
                'url': 'https://www.bescom.org/en/tenders',
                'verify_ssl': True
            },
            'delhi': {
                'url': 'https://www.delhi.gov.in/web/tenders',
                'verify_ssl': True
            },
        }
        # Apply overrides if present
        try:
            from pathlib import Path
            import json
            override_path = Path('config/state_seb_overrides.json')
            if override_path.exists():
                data = json.loads(override_path.read_text(encoding='utf-8'))
                for state, cfg in (data or {}).items():
                    if isinstance(cfg, dict) and 'url' in cfg:
                        self.state_seb_urls[state] = {
                            'url': cfg.get('url'),
                            'verify_ssl': bool(cfg.get('verify_ssl', True))
                        }
        except Exception:
            pass
    
    def scrape_all_states(self) -> List[Dict]:
        """Scrape all states with error handling."""
        
        all_tenders = []
        
        for state, config in self.state_seb_urls.items():
            try:
                tenders = self._scrape_state(state, config)
                all_tenders.extend(tenders)
                
                if tenders:
                    logger.info(f"[OK] {state}: Found {len(tenders)} tenders")
                else:
                    logger.warning(f"[WARN] {state}: No tenders found")
            
            except Exception as e:
                logger.warning(f"[WARN] {state}: {str(e)}")
        
        return all_tenders
    
    def _scrape_state(self, state: str, config: dict) -> List[Dict]:
        """Scrape individual state with SSL handling."""
        
        url = config['url']
        verify_ssl = config.get('verify_ssl', True)
        
        try:
            # DNS precheck
            try:
                from utils.reachability import host_from_url, can_resolve, should_skip_host, mark_unreachable
                host = host_from_url(url)
                if host:
                    if should_skip_host(host):
                        logger.warning(f"{state}: host in skip-cache {host}")
                        return []
                    if not can_resolve(host):
                        logger.warning(f"{state}: DNS unresolved for {host}")
                        mark_unreachable(host, reason='dns')
                        return []
            except Exception:
                pass
            from utils.http_client import http_get
            response = http_get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    'Accept': 'text/html,application/xhtml+xml',
                },
                timeout=30,
                verify=verify_ssl,  # Some states have SSL cert issues
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"{state}: Status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tenders = []
            
            # Find tender items (flexible selectors)
            items = (
                soup.find_all('tr', class_=lambda x: x and 'tender' in x.lower()) or
                soup.find_all('div', class_=lambda x: x and 'tender' in x.lower()) or
                soup.find_all('li')
            )
            
            for item in items:
                try:
                    text = item.get_text(strip=True)
                    
                    # Must contain cable keywords
                    if not self._has_cable_keywords(text):
                        continue
                    
                    tender = {
                        'source': f'State SEB - {state.replace("_", " ").title()}',
                        'tender_id': f"SEB-{state}-{hash(text[:100]) % 100000}",
                        'title': text[:200],
                        'description': text[:500],
                        'organization': f'{state.replace("_", " ").title()} Electricity Board',
                        'state': state,
                        'raw_data': text
                    }
                    
                    tenders.append(tender)
                
                except Exception as e:
                    continue
            
            return tenders
        
        except requests.exceptions.SSLError:
            # Try again without SSL verification
            logger.warning(f"{state}: SSL error, retrying without verification")
            
            try:
                response = requests.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=30,
                    verify=False
                )
                
                # Parse again...(simplified)
                return []
            
            except Exception as e:
                logger.error(f"{state}: Failed even without SSL: {str(e)}")
                return []
        
        except Exception as e:
            logger.error(f"{state}: {str(e)}")
            return []
    
    def _has_cable_keywords(self, text: str) -> bool:
        """Check for cable keywords."""
        
        cable_keywords = ['cable', 'wire', 'conductor', 'xlpe', 'pvc', 
                         'armored', 'transmission', 'distribution', 'power cable']
        
        text_lower = text.lower()
        
        return any(kw in text_lower for kw in cable_keywords)
