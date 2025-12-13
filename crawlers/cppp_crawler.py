import logging
import re
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

class CPPPCrawler:
    """
    Central Public Procurement Portal (CPPP / eProcure) lightweight crawler.
    - Targets public pages to discover active tenders with basic fields.
    - Conservative timeouts, resilient to structure changes.
    - Returns tenders normalized to our schema.
    """

    LIST_URLS = [
        "https://eprocure.gov.in/eprocure/app",
        "https://eprocure.gov.in/epublish/app",
    ]

    def __init__(self, timeout: int = 12, per_page_limit: int = 20):
        self.timeout = timeout
        self.per_page_limit = per_page_limit

    def _fetch(self, url: str) -> str:
        if not requests:
            logger.info("CPPP: 'requests' library not available; skipping")
            return ""
        try:
            from utils.http_client import http_get
            resp = http_get(
                url,
                headers={
                    "User-Agent": "CableRFPBot/1.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=self.timeout,
                verify=True,
            )
            if resp.status_code == 200 and isinstance(resp.text, str):
                return resp.text
            logger.warning(f"CPPP: Non-200 status for {url}: {resp.status_code}")
        except Exception as e:
            logger.info(f"CPPP: fetch failed for {url}: {e}")
        return ""

    def _parse(self, html: str, base_url: str) -> List[Dict]:
        if not BeautifulSoup:
            return []
        soup = BeautifulSoup(html, "html.parser")
        tenders: List[Dict] = []

        # Strategy 1: Table rows with likely tender listings
        tables = soup.find_all("table")
        for table in tables:
            for tr in table.find_all("tr"):
                try:
                    cols = tr.find_all(["td", "th"])
                    text = " ".join(c.get_text(strip=True) for c in cols)
                    if not text:
                        continue
                    if not any(k in text.lower() for k in ["tender", "bid", "nit", "rfp"]):
                        continue
                    a = tr.find("a")
                    href = a.get("href") if a else None
                    title = a.get_text(strip=True) if a and a.get_text(strip=True) else (text[:200])
                    url = urljoin(base_url, href) if href else base_url
                    deadline = self._extract_deadline(text)
                    tenders.append({
                        "source": "CPPP",
                        "tender_id": f"CPPP-{abs(hash(url+title)) % 1000000}",
                        "title": title,
                        "organization": self._extract_org(text) or "CPPP",
                        "deadline": deadline or None,
                        "estimated_value": 0,
                        "description": title,
                        "url": url,
                    })
                    if len(tenders) >= self.per_page_limit:
                        return tenders
                except Exception:
                    continue

        # Strategy 2: Generic anchors (fallback)
        for a in soup.find_all("a"):
            try:
                txt = a.get_text(strip=True) or ""
                href = a.get("href") or ""
                if not txt and not href:
                    continue
                blob = f"{txt} {href}".lower()
                if any(k in blob for k in ["tender", "nit", "rfp", "bid"]):
                    url = urljoin(base_url, href)
                    tenders.append({
                        "source": "CPPP",
                        "tender_id": f"CPPP-{abs(hash(url)) % 1000000}",
                        "title": txt or url,
                        "organization": "CPPP",
                        "deadline": None,
                        "estimated_value": 0,
                        "description": txt or url,
                        "url": url,
                    })
                    if len(tenders) >= self.per_page_limit:
                        break
            except Exception:
                continue

        return tenders

    def _extract_deadline(self, text: str) -> str:
        # Look for DD-MM-YYYY or DD/MM/YYYY or 'Month DD, YYYY HH:MM'
        from datetime import datetime
        candidates = []
        for pat in [
            r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",
            r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4}(?:\s+\d{1,2}:\d{2})?)",
        ]:
            m = re.search(pat, text)
            if m:
                candidates.append(m.group(1))
        for s in candidates:
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%B %d, %Y %H:%M", "%B %d, %Y"):
                try:
                    return datetime.strptime(s, fmt).isoformat() + "Z"
                except Exception:
                    continue
        return ""

    def _extract_org(self, text: str) -> str:
        # Heuristic: take fragment before 'tender' or first uppercase phrase
        m = re.search(r"([A-Za-z&()\-\s]{5,40})\s+tender", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()[:40]
        m = re.search(r"([A-Z][A-Za-z&()\-\s]{5,50})", text)
        return m.group(1).strip()[:50] if m else ""

    def scrape_tenders(self) -> List[Dict]:
        results: List[Dict] = []
        for url in self.LIST_URLS:
            html = self._fetch(url)
            if not html:
                continue
            parsed = self._parse(html, url)
            results.extend(parsed)
        logger.info(f"CPPP: scraped {len(results)} tenders")
        return results
