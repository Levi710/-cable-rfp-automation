import logging
import re
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class HtmlPortalCrawler:
    """
    Parse local HTML tender portal and return tenders in a normalized format.
    Default file: data/sample_websites/tender_portal.html
    """
    def __init__(self, html_path: str = "data/sample_websites/tender_portal.html"):
        self.html_path = Path(html_path)

    def _read(self) -> str:
        try:
            return self.html_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"HTML portal not available at {self.html_path}: {e}")
            return ""

    def _extract(self, html: str) -> List[Dict]:
        tenders: List[Dict] = []

        # Split into card blocks
        cards = re.split(r'<div\s+class=\"tender-card\"[^>]*>', html)[1:]
        for card in cards:
            try:
                tender_id = self._find_text(card, r'<span\s+class=\"tender-id\">(.*?)</span>')
                title = self._find_text(card, r'<h2\s+class=\"tender-title\">(.*?)</h2>')
                org = self._find_text(card, r'<p\s+class=\"tender-org\">(.*?)</p>')
                est_val_txt = self._find_detail(card, 'Estimated Value')
                deadline_txt = self._find_detail(card, 'Submission Deadline')
                qty_txt = self._find_detail(card, 'Quantity')

                estimated_value = self._parse_rupees(est_val_txt)
                deadline_iso = self._parse_deadline(deadline_txt)
                length_km = self._parse_length(qty_txt)

                tenders.append({
                    'source': 'HTML Portal',
                    'tender_id': tender_id or f"HTML-{abs(hash(title)) % 100000}",
                    'title': title,
                    'organization': (org or '').replace('\n', ' ').strip(),
                    'estimated_value': estimated_value,
                    'deadline': deadline_iso,
                    'length_km': length_km,
                    'description': title
                })
            except Exception as e:
                logger.debug(f"Failed to parse tender card: {e}")
                continue
        return tenders

    def _find_text(self, block: str, pattern: str) -> str:
        m = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ''

    def _find_detail(self, block: str, label: str) -> str:
        # Match <span class="detail-label">Label</span><span class="detail-value">Value</span>
        pattern = rf'<span\s+class=\"detail-label\">\s*{re.escape(label)}\s*</span>\s*<span\s+class=\"detail-value[^\"]*\">(.*?)</span>'
        m = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ''

    def _parse_rupees(self, text: str) -> float:
        # Supports formats like: Rs 125,000,000
        m = re.search(r'([\d,]+)', text.replace('\u00a0', ' '))
        if not m:
            return 0.0
        return float(m.group(1).replace(',', ''))

    def _parse_deadline(self, text: str) -> str:
        # Examples: "January 25, 2026 17:30 IST"
        # Convert to ISO; if parsing fails, return original
        try:
            # Normalize spaces
            t = re.sub(r'\s+', ' ', text).strip()
            # Remove timezone token but keep time
            t = t.replace(' IST', '')
            from datetime import datetime
            dt = datetime.strptime(t, '%B %d, %Y %H:%M')
            return dt.isoformat() + 'Z'
        except Exception:
            return text

    def _parse_length(self, text: str) -> float:
        # E.g., "500 Kilometers" => 500
        m = re.search(r'(\d+)', text)
        return float(m.group(1)) if m else 0.0

    def search_tenders(self) -> List[Dict]:
        html = self._read()
        if not html:
            return []
        tenders = self._extract(html)
        logger.info(f"HTML Portal: Parsed {len(tenders)} tenders")
        return tenders
