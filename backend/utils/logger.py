# /backend/utils/logger.py

from logging import config


def setup_logging(level: str = "INFO"):
    """
    Configures the root logger:
      - Console (stdout) at `level`
      - File at DEBUG (if log_file is provided)
      - Formatter shows timestamp, module, file:line, level and message
    """
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s "
                    # "| %(module)s "
                    "| %(filename)s:%(lineno)d "
                    "| %(levelname)s "
                    "| %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    config.dictConfig(LOGGING_CONFIG)
