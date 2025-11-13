"""Logger utility following DRY principle."""

import logging
from typing import Optional

from config.constants import AppConstants


class LoggerUtils:
    """Centralized logger creation and configuration."""

    @staticmethod
    def setup_logger(
        name: str,
        level: int = logging.INFO,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
    ) -> logging.Logger:
        """
        Create and configure a logger.

        Args:
            name: Logger name
            level: Logging level
            log_format: Custom log format (optional)
            date_format: Custom date format (optional)

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Set formatter
        formatter = logging.Formatter(
            log_format or AppConstants.LOG_FORMAT,
            datefmt=date_format or AppConstants.LOG_DATE_FORMAT,
        )
        console_handler.setFormatter(formatter)

        # Add handler
        logger.addHandler(console_handler)

        return logger

    @staticmethod
    def suppress_noisy_loggers():
        """Suppress logging from noisy third-party libraries."""
        noisy_loggers = ["httpx", "httpcore", "anyio"]
        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
