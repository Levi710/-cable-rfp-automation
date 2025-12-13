import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = 'postgresql://rfp_user:rfp_password@postgres:5432/cable_rfp'
    REDIS_URL: str = 'redis://redis:6379/0'
    QDRANT_URL: str = 'http://qdrant:6333'

    # Email
    EMAIL_IMAP_SERVER: str = 'imap.gmail.com'
    EMAIL_ADDRESS: str = ''
    EMAIL_PASSWORD: str = ''

    # OpenAI
    OPENAI_API_KEY: str = ''

    # System
    ENVIRONMENT: str = 'production'
    DEBUG: bool = False
    LOG_LEVEL: str = 'INFO'
    PORT: int = 8000

    # Crawlers
    GEM_BASE_URL: str = 'https://gem.gov.in/api/v1'
    CRAWL_INTERVAL_GEM_HOURS: int = 6
    CRAWL_INTERVAL_POWERGRID_HOURS: int = 12
    CRAWL_INTERVAL_STATE_SEB_HOURS: int = 12
    ENABLE_SCHEDULER: bool = True

    # Proxy Configuration (for accessing geo-restricted portals)
    PROXY_URL: str = ''  # e.g., 'http://proxy.company.com:8080' or 'socks5://127.0.0.1:1080'
    PROXY_USERNAME: str = ''
    PROXY_PASSWORD: str = ''
    VERIFY_SSL: bool = True  # Set to False if behind corporate proxy with SSL inspection
    HTTP_TIMEOUT: int = 30  # Request timeout in seconds

    # Crawler Source Control (disable unreachable sources to speed up discovery)
    ENABLE_NTPC: bool = True
    ENABLE_POWERGRID: bool = True
    ENABLE_STATE_SEB: bool = True
    ENABLE_GEM: bool = True
    ENABLE_CPPP: bool = True

    # Tracing
    JAEGER_AGENT_HOST: str = 'jaeger'

    class Config:
        env_file = '.env'
        extra = 'allow'

settings = Settings()

