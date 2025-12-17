import os
import logging
from typing import Optional, Dict

try:
    import requests  # type: ignore
except Exception:
    requests = None

logger = logging.getLogger(__name__)


def _proxies_from_env() -> Optional[Dict[str, str]]:
    """Build proxy configuration from environment variables."""
    proxy = os.environ.get('PROXY_URL', '')
    if not proxy:
        # If PROXY_URL not set, requests will still honor HTTP(S)_PROXY env vars
        return None
    
    # Check for authenticated proxy
    username = os.environ.get('PROXY_USERNAME', '')
    password = os.environ.get('PROXY_PASSWORD', '')
    
    if username and password:
        # Insert credentials into proxy URL
        # e.g., http://proxy:8080 -> http://user:pass@proxy:8080
        if '://' in proxy:
            protocol, rest = proxy.split('://', 1)
            proxy = f"{protocol}://{username}:{password}@{rest}"
        logger.debug("Using authenticated proxy")
    
    return {'http': proxy, 'https': proxy}


def http_get(url: str, *, headers: Optional[Dict[str, str]] = None, timeout: int = 30,
             verify: bool = True, allow_redirects: bool = True, auth=None):
    """
    Make HTTP GET request with proxy and SSL configuration support.
    
    Environment variables:
        PROXY_URL: Proxy URL (e.g., http://proxy:8080 or socks5://127.0.0.1:1080)
        PROXY_USERNAME: Proxy username for authenticated proxies
        PROXY_PASSWORD: Proxy password for authenticated proxies
        VERIFY_SSL: Set to 'false' to disable SSL verification (for corporate proxies)
        HTTP_TIMEOUT: Request timeout in seconds (default: 30)
    """
    if not requests:
        raise RuntimeError("requests library not installed")
    
    proxies = _proxies_from_env()
    
    # Check for SSL verification override
    verify_ssl = os.environ.get('VERIFY_SSL', 'true').lower() not in ('false', '0', 'no')
    if not verify_ssl:
        verify = False
        # Suppress SSL warnings when intentionally disabled
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Get timeout from environment if set
    env_timeout = os.environ.get('HTTP_TIMEOUT')
    if env_timeout:
        try:
            timeout = int(env_timeout)
        except ValueError:
            pass
    
    try:
        response = requests.get(
            url, 
            headers=headers or {}, 
            timeout=timeout, 
            verify=verify,
            allow_redirects=allow_redirects, 
            proxies=proxies, 
            auth=auth
        )
        logger.debug(f"HTTP GET {url} -> {response.status_code}")
        return response
    except requests.exceptions.ProxyError as e:
        logger.error(f"Proxy error for {url}: {e}")
        raise
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL error for {url}: {e}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error for {url}: {e}")
        raise

