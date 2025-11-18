import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    service_name: str = "yantra-ai-backend"
):
    """
    Setup structured logging for the application
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    if log_format.lower() == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    """
    return logging.getLogger(name)


class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records
    """
    def __init__(self, context: Dict[str, Any] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record):
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_request_logging():
    """
    Setup request logging middleware context
    """
    return ContextFilter({
        'service': 'yantra-ai-backend',
        'version': '1.0.0'
    })