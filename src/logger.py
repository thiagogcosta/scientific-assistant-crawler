import logging

from src.templates.singleton import Singleton

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)


class Logger(Singleton):
    def get_logger(self) -> logging.Logger:
        """Returns a logger instance with the name of the current module."""
        return logging.getLogger(__name__)
