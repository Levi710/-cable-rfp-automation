import socket
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict

_CACHE_PATH = Path('output') / 'connectivity' / 'host_skip_cache.json'
_DEFAULT_TTL_HOURS = int(os.environ.get('SKIP_TTL_HOURS', '6'))


def _now() -> datetime:
    # timezone-naive UTC ok for TTL comparisons here
    return datetime.utcnow()


def _load_cache() -> Dict[str, Dict]:
    try:
        if _CACHE_PATH.exists():
            data = json.loads(_CACHE_PATH.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_cache(cache: Dict[str, Dict]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding='utf-8')
    except Exception:
        pass


def host_from_url(url: str) -> Optional[str]:
    try:
        return urlparse(url).netloc
    except Exception:
        return None


def can_resolve(host: str) -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except Exception:
        return False


def should_skip_host(host: str) -> bool:
    """Return True if host is in skip cache and TTL not expired."""
    cache = _load_cache()
    entry = cache.get(host)
    if not entry:
        return False
    until = entry.get('until')
    if not until:
        return False
    try:
        dt = datetime.fromisoformat(until)
        if _now() < dt:
            return True
    except Exception:
        return False
    return False


def mark_unreachable(host: str, reason: str = 'dns', ttl_hours: Optional[int] = None) -> None:
    """Mark a host as unreachable for a TTL to avoid repeated lookups/requests."""
    ttl = ttl_hours if ttl_hours is not None else _DEFAULT_TTL_HOURS
    until = _now() + timedelta(hours=ttl)
    cache = _load_cache()
    cache[host] = {'until': until.isoformat(), 'reason': reason}
    _save_cache(cache)
