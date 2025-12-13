import logging
from logging.config import dictConfig

def setup_logging(level: str = "INFO"):
    config = {
        "version": 1,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default"
            }
        },
        "root": {
            "level": level,
            "handlers": ["console"]
        }
    }
    dictConfig(config)
