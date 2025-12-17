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

logger = logging.getLogger(__name__)

class NTPCCrawler:
    """
    NTPC crawler with fallback URLs and better error handling.
    """
    
    def __init__(self):
        # Multiple NTPC tender URLs - official eProcurement portal first
        self.urls = [
            'https://eprocurentpc.nic.in/nicgep/app',  # Official NTPC eProcurement Portal
            'https://ntpc.co.in/notice-inviting-tenders',  # Main NTPC tender page
            'https://www.ntpc.co.in/en/tenders',
            'https://ntpctender.com/',
            'https://www.ntpc.co.in/tenders-notices',
        ]
    
    def scrape_tenders(self) -> List[Dict]:
        """Try all URLs until one works."""
        if not requests or not BeautifulSoup:
            logger.info("NTPC: missing 'requests' or 'bs4'; skipping")
            return []
        all_found: List[Dict] = []
        for url in self.urls:
            try:
                # DNS precheck
                try:
                    from utils.reachability import host_from_url, can_resolve, should_skip_host, mark_unreachable
                    host = host_from_url(url)
                    if host:
                        if should_skip_host(host):
                            logger.info(f"NTPC: host in skip-cache {host}; skipping")
                            continue
                        if not can_resolve(host):
                            logger.info(f"NTPC: DNS unresolved for {host}; skipping")
                            mark_unreachable(host, reason='dns')
                            continue
                except Exception:
                    pass
                logger.info(f"Trying NTPC URL: {url}")
                from utils.http_client import http_get
                response = http_get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=20,
                    verify=True
                )
                if response.status_code == 200:
                    tenders = self._parse_tenders(response.text, url)
                    if tenders:
                        logger.info(f"NTPC ({url}): Found {len(tenders)} tenders")
                        all_found.extend(tenders)
            except Exception as e:
                logger.warning(f"NTPC ({url}): {str(e)}")
        if not all_found:
            logger.warning("NTPC: No tenders parsed")
        return all_found
    
    def _parse_tenders(self, html: str, base_url: str) -> List[Dict]:
        """Parse tenders from HTML."""
        soup = BeautifulSoup(html, 'html.parser') if BeautifulSoup else None
        if not soup:
            return []
        tenders: List[Dict] = []
        # Prefer rows or cards containing tender info
        items = soup.find_all(['div', 'tr', 'li'], class_=lambda x: x and 'tender' in x.lower())
        if not items:
            items = soup.find_all(['tr'])
        for item in items:
            try:
                title_el = item.find(['h3', 'h4', 'a']) or item.find('a')
                title = title_el.get_text(strip=True) if title_el else item.get_text(strip=True)[:200]
                href = title_el.get('href') if title_el and title_el.has_attr('href') else ''
                url = urljoin(base_url, href) if href else base_url
                text = item.get_text(" ", strip=True)
                deadline = self._extract_deadline(text)
                tender = {
                    'source': 'NTPC',
                    'tender_id': f"NTPC-{abs(hash(url+title)) % 1000000}",
                    'title': title,
                    'description': text[:500],
                    'organization': 'NTPC Limited',
                    'deadline': deadline or None,
                    'url': url,
                    'raw_data': text
                }
                if self._is_cable_tender(tender):
                    tenders.append(tender)
            except Exception:
                continue
        return tenders
    
    def _is_cable_tender(self, tender: dict) -> bool:
        """Check if cable-related."""
        cable_keywords = ['cable', 'wire', 'conductor', 'xlpe', 'pvc', 'power', 'electrical', 'kv']
        text = (tender.get('title', '') + ' ' + tender.get('description', '')).lower()
        return any(kw in text for kw in cable_keywords)

    def _extract_deadline(self, text: str) -> str:
        from datetime import datetime
        # Look for date-time patterns commonly used on NTPC portals
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
