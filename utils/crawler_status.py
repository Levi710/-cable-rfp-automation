"""
Crawler Status Logger - Production Monitoring Utility

Logs crawler status to JSON file for monitoring which sources are working/failing.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Output path for status log
STATUS_LOG_PATH = Path('output/crawler_status.json')


class CrawlerStatusLogger:
    """
    Logs crawler source status for production monitoring.
    
    Usage:
        status_logger = CrawlerStatusLogger()
        status_logger.log_source('NTPC', success=True, tenders_found=5)
        status_logger.log_source('POWERGRID', success=False, error='DNS resolution failed')
        status_logger.save()
    """
    
    def __init__(self):
        self.run_timestamp = datetime.now().isoformat()
        self.sources: Dict[str, Dict] = {}
        self.total_tenders = 0
    
    def log_source(
        self, 
        source_name: str, 
        success: bool, 
        tenders_found: int = 0,
        urls_tried: Optional[List[str]] = None,
        error: Optional[str] = None,
        latency_ms: Optional[int] = None
    ):
        """Log status for a crawler source."""
        self.sources[source_name] = {
            'success': success,
            'tenders_found': tenders_found,
            'urls_tried': urls_tried or [],
            'error': error,
            'latency_ms': latency_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.total_tenders += tenders_found
            logger.info(f"[OK] {source_name}: {tenders_found} tenders discovered")
        else:
            logger.warning(f"[FAILED] {source_name}: {error or 'Failed'}")
    
    def get_summary(self) -> Dict:
        """Get summary of all sources."""
        successful = [s for s, d in self.sources.items() if d['success']]
        failed = [s for s, d in self.sources.items() if not d['success']]
        
        return {
            'run_timestamp': self.run_timestamp,
            'total_sources': len(self.sources),
            'successful_sources': len(successful),
            'failed_sources': len(failed),
            'total_tenders_discovered': self.total_tenders,
            'successful': successful,
            'failed': failed,
            'sources': self.sources
        }
    
    def save(self, path: Optional[Path] = None):
        """Save status log to JSON file."""
        output_path = path or STATUS_LOG_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        summary = self.get_summary()
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Crawler status saved to: {output_path}")
        return summary
    
    def print_summary(self):
        """Print summary to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("CRAWLER STATUS SUMMARY")
        print("=" * 60)
        print(f"Run Time: {summary['run_timestamp']}")
        print(f"Sources Tried: {summary['total_sources']}")
        print(f"Successful: {summary['successful_sources']}")
        print(f"Failed: {summary['failed_sources']}")
        print(f"Total Tenders: {summary['total_tenders_discovered']}")
        print()
        
        if summary['successful']:
            print("Working Sources:")
            for source in summary['successful']:
                data = summary['sources'][source]
                print(f"   - {source}: {data['tenders_found']} tenders")
        
        if summary['failed']:
            print("\nFailed Sources:")
            for source in summary['failed']:
                data = summary['sources'][source]
                print(f"   - {source}: {data['error'] or 'Unknown error'}")
        
        print("=" * 60 + "\n")


# Global instance for easy access
_status_logger: Optional[CrawlerStatusLogger] = None


def get_status_logger() -> CrawlerStatusLogger:
    """Get or create global status logger instance."""
    global _status_logger
    if _status_logger is None:
        _status_logger = CrawlerStatusLogger()
    return _status_logger


def reset_status_logger():
    """Reset status logger for new run."""
    global _status_logger
    _status_logger = CrawlerStatusLogger()
    return _status_logger
