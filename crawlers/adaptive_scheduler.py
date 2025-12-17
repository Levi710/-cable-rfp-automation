"""
INNOVATION 1: Intelligent Adaptive Web Crawler with Dynamic Scheduling
Learns crawl frequency from hit rates and adjusts automatically
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class AdaptiveScheduler:
    """
    Adaptive scheduling that learns from crawler performance.
    Adjusts crawl intervals based on:
    - Hit rate (% of relevant tenders)
    - Success rate
    - Response time
    """
    
    def __init__(self):
        # Default in-memory state
        self.sources_metrics = {
            'gem': {
                'hit_rate': 0.82,
                'success_rate': 0.98,
                'response_time_ms': 150,
                'last_crawl': None,
                'crawl_history': []
            },
            'powergrid': {
                'hit_rate': 0.78,
                'success_rate': 0.95,
                'response_time_ms': 2500,
                'last_crawl': None,
                'crawl_history': []
            },
            'state_seb': {
                'hit_rate': 0.65,
                'success_rate': 0.92,
                'response_time_ms': 3000,
                'last_crawl': None,
                'crawl_history': []
            },
            'ntpc': {
                'hit_rate': 0.70,
                'success_rate': 0.93,
                'response_time_ms': 2000,
                'last_crawl': None,
                'crawl_history': []
            }
        }
        # Persistence file
        self._state_path = Path('output') / 'adaptive_metrics.json'
        self._load_state()
    
    def calculate_adaptive_interval(self, source: str) -> int:
        """
        Dynamically calculate crawl interval based on performance.
        
        Algorithm:
        productivity_score = (hit_rate * 0.4) + (success_rate * 0.4) + (response_normalized * 0.2)
        interval = 24 - (productivity_score * 20)  # Maps to 4-24 hours
        """
        
        metrics = self.sources_metrics.get(source, {})
        
        hit_rate = metrics.get('hit_rate', 0.5)
        success_rate = metrics.get('success_rate', 0.9)
        response_time = metrics.get('response_time_ms', 2000)
        
        # Normalize response time (2000ms = 1.0)
        response_normalized = min(response_time / 2000, 1.0)
        
        # Calculate productivity score
        productivity = (hit_rate * 0.4) + (success_rate * 0.4) + ((1 - response_normalized) * 0.2)
        
        # Map to interval (high productivity = shorter interval)
        interval = int(24 - (productivity * 20))
        
        # Clamp to 4-24 hours
        return max(4, min(24, interval))
    
    def record_crawl(self, source: str, tenders_found: int, success: bool, response_time_ms: int):
        """Record crawl result for learning."""
        
        metrics = self.sources_metrics[source]
        
        # Update success rate
        crawl_history = metrics['crawl_history']
        crawl_history.append({'success': success, 'tenders': tenders_found})
        
        if len(crawl_history) > 100:
            crawl_history.pop(0)
        
        # Calculate rolling hit rate
        total_tenders = sum(c['tenders'] for c in crawl_history)
        successful_crawls = sum(1 for c in crawl_history if c['success'])
        
        metrics['hit_rate'] = total_tenders / len(crawl_history) if crawl_history else 0.5
        metrics['success_rate'] = successful_crawls / len(crawl_history) if crawl_history else 0.9
        metrics['response_time_ms'] = response_time_ms
        metrics['last_crawl'] = datetime.now()
        
        # Persist updated state
        self._save_state()
        
        logger.info(f"{source}: Hit rate={metrics['hit_rate']:.2%}, Success={metrics['success_rate']:.2%}")
    
    def should_crawl_now(self, source: str) -> bool:
        """Check if source is due for crawl."""
        
        metrics = self.sources_metrics.get(source, {})
        last_crawl = metrics.get('last_crawl')
        
        if not last_crawl:
            return True  # First time
        # If stored as string, parse to datetime
        if isinstance(last_crawl, str):
            try:
                metrics['last_crawl'] = datetime.fromisoformat(last_crawl)
                last_crawl = metrics['last_crawl']
            except Exception:
                last_crawl = None
                metrics['last_crawl'] = None
                return True
        
        interval = self.calculate_adaptive_interval(source)
        elapsed_hours = (datetime.now() - last_crawl).total_seconds() / 3600
        
        return elapsed_hours >= interval
    
    def _load_state(self):
        """Load metrics from JSON if available."""
        try:
            if self._state_path.exists():
                data = json.loads(self._state_path.read_text(encoding='utf-8'))
                loaded = {}
                for src, m in data.items():
                    lm = m.get('last_crawl')
                    if lm:
                        try:
                            m['last_crawl'] = datetime.fromisoformat(lm)
                        except Exception:
                            m['last_crawl'] = None
                    loaded[src] = m
                # Merge with defaults to keep structure
                for k in self.sources_metrics.keys():
                    if k in loaded:
                        self.sources_metrics[k].update(loaded[k])
        except Exception as e:
            logger.info(f"AdaptiveScheduler: failed to load state: {e}")
    
    def _save_state(self):
        """Persist metrics to JSON (with ISO datetimes)."""
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            out = {}
            for src, m in self.sources_metrics.items():
                mm = dict(m)
                lc = mm.get('last_crawl')
                if isinstance(lc, datetime):
                    mm['last_crawl'] = lc.isoformat()
                out[src] = mm
            self._state_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
        except Exception as e:
            logger.info(f"AdaptiveScheduler: failed to save state: {e}")
