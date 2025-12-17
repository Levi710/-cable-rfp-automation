try:
    import requests
except Exception:  # pragma: no cover
    requests = None
try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore
from typing import List, Dict
import logging
import re
from urllib.parse import urljoin
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)

class POWERGRIDCrawler:
    """
    POWERGRID crawler with resilient parsing and optional dependencies.
    Falls back to demo feed if scraping fails or network is unavailable.
    """
    
    def __init__(self, timeout: int = 20, per_page_limit: int = 30):
        # Official PRANIT portal first, then fallbacks
        self.urls = [
            'https://eprocure.powergrid.in/nicgep/app',  # PRANIT - Official POWERGRID eProcurement
            'https://www.powergrid.in/notice-inviting-tenders',  # Main tender notices page
            'https://www.powergrid.in/tenders',
            'https://www.powergridindia.com/tenders',
            'https://etender.powergrid.co.in/nicgep/app',
        ]
        self.timeout = timeout
        self.per_page_limit = per_page_limit
    
    def _load_demo(self) -> List[Dict]:
        try:
            demo_path = Path(__file__).resolve().parent.parent / 'data' / 'feeds' / 'powergrid_demo.json'
            with open(demo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tenders = data.get('tenders', [])
            logger.info(f"POWERGRID Demo: Loaded {len(tenders)} demo tenders")
            return tenders
        except Exception as e:
            logger.info(f"POWERGRID Demo fallback not available: {e}")
            return []
    
    def scrape_tenders(self) -> List[Dict]:
        """Scrape from POWERGRID URLs if dependencies are available; fallback to demo on failure."""
        disable_demo = os.getenv('DISABLE_DEMO_SOURCES', 'false').lower() in ('1', 'true', 'yes')
        if not requests or not BeautifulSoup:
            if disable_demo:
                logger.info("POWERGRID: missing 'requests' or 'bs4' and DISABLE_DEMO_SOURCES=1; returning no results")
                return []
            logger.info("POWERGRID: missing 'requests' or 'bs4'; using demo tenders")
            return self._load_demo()
        all_tenders: List[Dict] = []
        for url in self.urls:
            try:
                tenders = self._scrape_url(url)
                all_tenders.extend(tenders)
                if tenders:
                    logger.info(f"POWERGRID ({url}): Found {len(tenders)} tenders")
            except Exception as e:
                # DNS / network errors common in restricted environments
                msg = f"POWERGRID ({url}): {e}"
                if disable_demo:
                    logger.info(msg + "; demo disabled; continuing without fallback")
                else:
                    logger.info(msg + "; using demo fallback")
                    demo = self._load_demo()
                    if demo:
                        all_tenders.extend(demo)
                        break
        if not all_tenders and not disable_demo:
            # If scraping yielded nothing, try demo once (unless disabled)
            demo = self._load_demo()
            if demo:
                return demo
        return all_tenders
    
    def _scrape_url(self, url: str) -> List[Dict]:
        """Scrape specific URL with flexible selectors."""
        try:
            from utils.http_client import http_get
            resp = http_get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                },
                timeout=self.timeout,
                verify=True,
            )
            if resp.status_code != 200:
                logger.warning(f"POWERGRID {url} -> {resp.status_code}")
                return []
            soup = BeautifulSoup(resp.text, 'html.parser') if BeautifulSoup else None
            if not soup:
                return []
            tenders: List[Dict] = []
            # Strategy 1: elements with 'tender' in class
            items = soup.find_all(['div', 'tr', 'li'], class_=lambda x: x and 'tender' in x.lower())
            # Strategy 2: rows in any tables
            if not items:
                for table in soup.find_all('table'):
                    items.extend(table.find_all('tr'))
            # Strategy 3: generic list items
            if not items:
                items = soup.find_all('li')
            for item in items:
                try:
                    td = self._parse_item(item, url)
                    if td and self._is_cable_tender(td):
                        tenders.append(td)
                        if len(tenders) >= self.per_page_limit:
                            break
                except Exception:
                    continue
            if not tenders:
                logger.debug(f"POWERGRID page had no tender-like items: {url}")
            return tenders
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _parse_item(self, item, base_url: str) -> Dict:
        text = item.get_text(" ", strip=True)
        title_el = item.find(['h3', 'h4', 'h5', 'strong', 'b', 'a']) or item.find('a')
        title = title_el.get_text(strip=True) if title_el else (text[:200] if text else '')
        link_el = item.find('a')
        href = link_el.get('href') if link_el and link_el.has_attr('href') else ''
        url = urljoin(base_url, href) if href else base_url
        value = self._extract_value(text)
        deadline = self._extract_deadline(text)
        return {
            'source': 'POWERGRID',
            'tender_id': f"PG-{abs(hash(url+title)) % 1000000}",
            'title': title,
            'description': text[:500],
            'organization': 'POWERGRID Corporation',
            'estimated_value': value,
            'deadline': deadline or None,
            'url': url,
            'raw_data': text,
        }
    
    def _extract_value(self, text: str) -> float:
        patterns = [
            r'₹\s*([\d,\.]+)\s*crore',
            r'Rs\.?\s*([\d,\.]+)\s*(?:crore|cr)',
            r'INR\s*([\d,\.]+)\s*(?:crore|cr)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = m.group(1).replace(',', '')
                try:
                    return float(v) * 10_000_000
                except Exception:
                    return 0.0
        return 0.0
    
    def _extract_deadline(self, text: str) -> str:
        from datetime import datetime
        for pat in [
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}\s*\d{1,2}:\d{2})\b",
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",
            r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2})?)",
        ]:
            m = re.search(pat, text)
            if not m:
                continue
            s = m.group(1)
            for fmt in ("%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y", "%d/%m/%Y", "%B %d, %Y %H:%M", "%B %d, %Y"):
                try:
                    return datetime.strptime(s, fmt).isoformat() + 'Z'
                except Exception:
                    continue
        return ''
    
    def _is_cable_tender(self, tender: dict) -> bool:
        cable_keywords = ['cable', 'wire', 'conductor', 'xlpe', 'pvc', 'transmission', 'power', 'electrical', 'hv', 'kv']
        text = (tender.get('title', '') + ' ' + tender.get('description', '')).lower()
        matches = sum(1 for kw in cable_keywords if kw in text)
        return matches >= 2
