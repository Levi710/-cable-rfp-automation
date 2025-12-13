import logging
from apscheduler.schedulers.background import BackgroundScheduler
from crawlers.unified_crawler import UnifiedCrawler

logger = logging.getLogger(__name__)

class CrawlScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.crawler = UnifiedCrawler()

    def start(self):
        # Schedule crawls (can be loaded from envs)
        self.scheduler.add_job(self.crawl_all, 'interval', hours=6, id='gem')
        self.scheduler.add_job(self.crawl_all, 'interval', hours=12, id='powergrid')
        self.scheduler.add_job(self.crawl_all, 'interval', hours=12, id='state_seb')
        self.scheduler.add_job(self.crawl_all, 'interval', minutes=60, id='email')
        self.scheduler.start()
        logger.info("Crawler scheduler started")

    def crawl_all(self):
        try:
            # Run asynchronously from a sync scheduler context
            import asyncio
            asyncio.run(self.crawler.discover_all_tenders())
        except Exception as e:
            logger.error(f"Scheduled crawl error: {e}")
