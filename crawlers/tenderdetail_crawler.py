import logging
from typing import List, Dict
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

from pathlib import Path
import json
import re
import os

class TenderDetailCrawler:
    """
    Crawler for https://www.tenderdetail.com/ (listing pages only, behind a feature flag).
    - Polite headers, short timeouts, and strict error handling.
    - Extracts tender-like items and normalizes fields where possible.
    - Falls back to demo feed if network or parsing fails.
    """

    BASE_URL = "https://www.tenderdetail.com/"

    def __init__(self, timeout: int = 10, per_page_limit: int = 20):
        self.timeout = timeout
        self.per_page_limit = per_page_limit

    def _load_demo(self) -> List[Dict]:
        try:
            demo_path = Path(__file__).resolve().parent.parent / 'data' / 'feeds' / 'tenderdetail_demo.json'
            data = json.loads(demo_path.read_text(encoding='utf-8'))
            tenders = data.get('tenders', [])
            logger.info(f"TenderDetail Demo: Loaded {len(tenders)} demo tenders")
            return tenders
        except Exception as e:
            logger.info(f"TenderDetail Demo not available: {e}")
            return []

    def _fetch(self, url: str) -> str:
        if not requests:
            return ""
        try:
            from utils.http_client import http_get
            resp = http_get(
                url,
                headers={'User-Agent': 'CableRFPBot/1.0', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
                timeout=self.timeout,
                verify=True,
            )
            if resp.status_code == 200 and isinstance(resp.text, str):
                return resp.text
        except Exception as e:
            logger.info(f"TenderDetail fetch failed: {e}")
        return ""

    def _parse_list(self, html: str, base_url: str) -> List[Dict]:
        if not BeautifulSoup or not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        tenders: List[Dict] = []
        # Heuristic: find items that look like tender cards/rows
        items = soup.find_all(['div','li','tr'])
        for el in items:
            try:
                text = el.get_text(" ", strip=True)
                if not text:
                    continue
                blob = text.lower()
                # Look for cable-related hints
                if not any(k in blob for k in ['cable', 'wire', 'conductor', 'xlpe', 'pvc']):
                    continue
                a = el.find('a')
                href = a.get('href') if a and a.has_attr('href') else ''
                title = a.get_text(strip=True) if a and a.get_text(strip=True) else text[:200]
                org = ''
                # crude org extraction
                m = re.search(r'by\s*([A-Za-z][A-Za-z\s&\-]{3,60})', text, re.IGNORECASE)
                if m:
                    org = m.group(1).strip()
                deadline = ''
                m = re.search(r'(\d{1,2}[\-/]\d{1,2}[\-/]\d{4})', text)
                if m:
                    # keep as is; SalesAgent handles parsing/fallback
                    deadline = m.group(1)
                url = urljoin(base_url, href) if href else base_url
                tender_id = f"TD-{abs(hash(url+title)) % 1000000}"
                tenders.append({
                    'source': 'TenderDetail',
                    'tender_id': tender_id,
                    'title': title,
                    'organization': org or 'TenderDetail',
                    'deadline': deadline or None,
                    'estimated_value': 0,
                    'description': title,
                    'url': url
                })
                if len(tenders) >= self.per_page_limit:
                    break
            except Exception:
                continue
        return tenders

    def scrape_tenders(self) -> List[Dict]:
        # For safety, only hit the home page (listing) unless configured otherwise
        disable_demo = os.getenv('DISABLE_DEMO_SOURCES', 'false').lower() in ('1', 'true', 'yes')
        html = self._fetch(self.BASE_URL)
        if not html:
            if disable_demo:
                logger.info("TenderDetail: no HTML fetched and demo disabled; returning no results")
                return []
            demo = self._load_demo()
            return demo
        parsed = self._parse_list(html, self.BASE_URL)
        if parsed:
            return parsed
        # fallback to demo if nothing parsed (unless disabled)
        if disable_demo:
            return []
        return self._load_demo()
