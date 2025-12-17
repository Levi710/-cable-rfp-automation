import time
import logging
from collections import deque

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Track crawler performance metrics over time."""
    def __init__(self, window: int = 100):
        self.history = deque(maxlen=window)

    def record(self, source: str, tenders: int, success: bool, ms: int):
        self.history.append({
            'source': source,
            'tenders': tenders,
            'success': success,
            'response_ms': ms,
            'ts': time.time()
        })

    def summary(self):
        if not self.history:
            return {}
        total = len(self.history)
        tenders = sum(h['tenders'] for h in self.history)
        success = sum(1 for h in self.history if h['success'])
        avg_ms = sum(h['response_ms'] for h in self.history) / total
        return {
            'events': total,
            'tenders_found': tenders,
            'success_rate': success / total,
            'avg_response_ms': avg_ms
        }
