"""
Multi-tier caching utility using Redis.
Provides caching for tender discovery and specifications.
"""

import json
import logging
import os
from typing import Optional, Any, List
import redis
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Prometheus metrics for cache operations
CACHE_HITS = Counter('cache_hits_total', 'Total cache hits', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses', ['cache_type'])

# Redis client singleton
_redis_client = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        try:
            redis_host = os.environ.get('REDIS_HOST', 'redis')
            redis_port = int(os.environ.get('REDIS_PORT', 6379))
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis client connected to {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    return _redis_client


def cache_get(key: str, cache_type: str = 'general') -> Optional[Any]:
    """
    Get value from cache.
    
    Args:
        key: Cache key
        cache_type: Type of cache for metrics (e.g. 'tenders', 'specs')
        
    Returns:
        Cached value or None if not found
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value is not None:
            CACHE_HITS.labels(cache_type=cache_type).inc()
            logger.debug(f"Cache HIT for key: {key}")
            return json.loads(value)
        else:
            CACHE_MISSES.labels(cache_type=cache_type).inc()
            logger.debug(f"Cache MISS for key: {key}")
            return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        CACHE_MISSES.labels(cache_type=cache_type).inc()
        return None


def cache_set(key: str, value: Any, ttl: int = 3600, cache_type: str = 'general') -> bool:
    """
    Set value in cache.
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 1 hour)
        cache_type: Type of cache for metrics
        
    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """
    Delete value from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        logger.debug(f"Cache DELETE for key: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


def cache_tender_discovery(source: str, tenders: List[dict], ttl: int = 1800) -> bool:
    """
    Cache tender discovery results.
    
    Args:
        source: Source name (e.g. 'GeM', 'POWERGRID')
        tenders: List of tender dictionaries
        ttl: Time to live in seconds (default: 30 minutes)
        
    Returns:
        True if cached successfully
    """
    key = f"tenders:discovery:{source}"
    return cache_set(key, tenders, ttl=ttl, cache_type='tenders')


def get_cached_tender_discovery(source: str) -> Optional[List[dict]]:
    """
    Get cached tender discovery results.
    
    Args:
        source: Source name
        
    Returns:
        List of cached tenders or None
    """
    key = f"tenders:discovery:{source}"
    return cache_get(key, cache_type='tenders')


def cache_tender_specs(tender_id: str, specs: dict, ttl: int = 7200) -> bool:
    """
    Cache parsed tender specifications.
    
    Args:
        tender_id: Tender ID
        specs: Parsed specifications dictionary
        ttl: Time to live in seconds (default: 2 hours)
        
    Returns:
        True if cached successfully
    """
    key = f"tenders:specs:{tender_id}"
    return cache_set(key, specs, ttl=ttl, cache_type='specs')


def get_cached_tender_specs(tender_id: str) -> Optional[dict]:
    """
    Get cached tender specifications.
    
    Args:
        tender_id: Tender ID
        
    Returns:
        Cached specifications or None
    """
    key = f"tenders:specs:{tender_id}"
    return cache_get(key, cache_type='specs')


def invalidate_tender_cache(tender_id: str) -> bool:
    """
    Invalidate all cache entries for a tender.
    
    Args:
        tender_id: Tender ID
        
    Returns:
        True if invalidated successfully
    """
    specs_key = f"tenders:specs:{tender_id}"
    return cache_delete(specs_key)
