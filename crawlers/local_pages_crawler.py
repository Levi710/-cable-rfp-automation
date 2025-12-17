import logging
import json
from pathlib import Path
from typing import List, Dict

from crawlers.html_portal_crawler import HtmlPortalCrawler

logger = logging.getLogger(__name__)

class LocalPagesCrawler:
    """
    Parse a list of local/sample HTML pages defined in config/sample_pages.json
    using HtmlPortalCrawler's parsing logic.
    """

    def __init__(self, config_path: str = 'config/sample_pages.json'):
        self.config_path = Path(config_path)

    def _load_pages(self) -> List[Path]:
        try:
            cfg = json.loads(self.config_path.read_text(encoding='utf-8'))
            pages = cfg.get('pages', [])
            return [Path(p) for p in pages if isinstance(p, str)]
        except Exception as e:
            logger.info(f"LocalPagesCrawler: cannot read {self.config_path}: {e}")
            return []

    def scrape(self) -> List[Dict]:
        tenders: List[Dict] = []
        for p in self._load_pages():
            try:
                if not p.exists():
                    logger.info(f"Local page missing: {p}")
                    continue
                crawler = HtmlPortalCrawler(html_path=str(p))
                page_tenders = crawler.search_tenders()
                tenders.extend(page_tenders)
            except Exception as e:
                logger.info(f"Local page failed ({p}): {e}")
        if tenders:
            logger.info(f"LocalPagesCrawler: Parsed {len(tenders)} tenders from sample pages")
        return tenders
