import logging
import re
import json
from typing import List, Dict
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

class UrlListCrawler:
    """
    Fetch a predefined list of procurement URLs and extract tender-like links.
    - Reads config/seed_urls.json {"urls": [ ... ]}
    - For each page, finds anchor tags with keywords: tender, bid, nit, eproc, etender, rfp
    - Attempts to parse a nearby or page-wide deadline date; otherwise leaves deadline None
    - Returns a normalized list of tender dicts
    """

    KEYWORDS = [
        'tender', 'bid', 'nit', 'procure', 'eproc', 'etender', 'rfp'
    ]

    DATE_PATTERNS = [
        # 25-01-2026 or 25/01/2026
        r'(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})',
        # January 25, 2026 17:30 or January 25, 2026
        r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2})?)'
    ]

    def __init__(self, url_list_path: str = 'config/seed_urls.json', timeout: int = 10, per_domain_limit: int = 10):
        self.url_list_path = url_list_path
        self.timeout = timeout
        self.per_domain_limit = per_domain_limit

    def _load_urls(self) -> List[str]:
        try:
            with open(self.url_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('urls', [])
        except Exception as e:
            logger.warning(f"UrlListCrawler: cannot read {self.url_list_path}: {e}")
            return []

    def _fetch(self, url: str) -> str:
        if not requests:
            logger.warning("UrlListCrawler: requests not available; skipping fetch")
            return ''
        # DNS precheck to avoid repeated connection errors
        try:
            from utils.reachability import host_from_url, can_resolve, should_skip_host, mark_unreachable
            host = host_from_url(url)
            if host:
                if should_skip_host(host):
                    logger.info(f"UrlListCrawler: host in skip-cache {host}; skipping")
                    return ''
                if not can_resolve(host):
                    logger.info(f"UrlListCrawler: DNS unresolved for {host}; skipping")
                    mark_unreachable(host, reason='dns')
                    return ''
        except Exception:
            pass
        try:
            from utils.http_client import http_get
            resp = http_get(url, headers={'User-Agent': 'CableRFPBot/1.0'}, timeout=self.timeout)
            if resp.status_code == 200 and isinstance(resp.text, str):
                return resp.text
            logger.warning(f"UrlListCrawler: non-200 for {url}: {resp.status_code}")
        except Exception as e:
            logger.info(f"UrlListCrawler: fetch failed for {url}: {e}")
        return ''

    def _extract_links(self, html: str, base: str) -> List[Dict]:
        tenders: List[Dict] = []
        # Find anchors
        for m in re.finditer(r'<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
            href = m.group(1)
            text = re.sub(r'<[^>]+>', '', m.group(2) or '').strip()
            full_url = urljoin(base, href)
            if not any(k in (href.lower() + ' ' + text.lower()) for k in self.KEYWORDS):
                continue
            # Compose candidate
            tenders.append({
                'url': full_url,
                'title': text or full_url,
            })
        return tenders

    def _guess_deadline(self, html: str) -> str:
        # Try multiple patterns; return ISO if possible
        from datetime import datetime
        for pat in self.DATE_PATTERNS:
            m = re.search(pat, html, re.IGNORECASE)
            if not m:
                continue
            s = m.group(1)
            for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y %H:%M', '%B %d, %Y'):
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.isoformat() + 'Z'
                except Exception:
                    continue
        return ''

    def search_tenders(self) -> List[Dict]:
        # If requests is unavailable, skip with a single log (avoid per-URL spam)
        if not requests:
            logger.info("UrlListCrawler: 'requests' not available; skipping seed URL crawl")
            return []
        urls = self._load_urls()
        results: List[Dict] = []
        per_domain_count: Dict[str, int] = {}
        for url in urls:
            domain = urlparse(url).netloc
            html = self._fetch(url)
            if not html:
                continue
            links = self._extract_links(html, url)
            deadline_iso = self._guess_deadline(html)
            for link in links:
                if per_domain_count.get(domain, 0) >= self.per_domain_limit:
                    break
                tender_id = f"URL-{abs(hash(link['url'])) % 1000000}"
                results.append({
                    'source': f'URL:{domain}',
                    'tender_id': tender_id,
                    'title': link['title'],
                    'organization': domain,
                    'deadline': deadline_iso or None,
                    'estimated_value': 0,
                    'description': link['url']
                })
                per_domain_count[domain] = per_domain_count.get(domain, 0) + 1
        logger.info(f"UrlListCrawler: Extracted {len(results)} tenders from {len(urls)} URLs")
        return results
