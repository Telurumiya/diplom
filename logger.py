import logging
import time
import uuid
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional



class CustomFormatter(logging.Formatter):
    """Custom formatter that handles optional props."""

    def format(self, record):
        if not hasattr(record, "props"):
            record.props = ""
        return super().format(record)


LOG_FORMAT = "%(asctime)s.%(msecs)03d - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s%(props)s"
DATE_FORMAT = "%d-%b-%y %H:%M:%S"


class LogHandler(ABC):
    """Abstract base class for log handlers."""

    @abstractmethod
    def configure(self) -> logging.Handler:
        """Configures and returns the log handler."""
        raise NotImplementedError


class ConsoleHandler(LogHandler):
    """Handler for outputting logs to the console."""

    def configure(self) -> logging.StreamHandler:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = CustomFormatter(LOG_FORMAT, DATE_FORMAT)
        formatter.default_msec_format = "%s.%03d"
        handler.setFormatter(formatter)
        return handler




class LoggerFactory:
    """Factory for creating loggers."""

    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}

    def get_logger(
        self, name: str, handlers: Optional[List[LogHandler]] = None
    ) -> logging.Logger:
        """Creates or returns an existing logger with the specified handlers."""
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if handlers:
            for handler in handlers:
                logger.addHandler(handler.configure())

        self.loggers[name] = logger
        return logger


logger_factory = LoggerFactory()
app_handlers = [ConsoleHandler()]
app_logger = logger_factory.get_logger("app", handlers=app_handlers)
