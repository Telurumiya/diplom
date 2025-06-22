import logging
import time
import uuid
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import get_settings

settings = get_settings()


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
        handler.setLevel(settings.LOG_LEVEL)
        formatter = CustomFormatter(LOG_FORMAT, DATE_FORMAT)
        formatter.default_msec_format = "%s.%03d"
        handler.setFormatter(formatter)
        return handler


class FileHandler(LogHandler):
    """Handler for writing logs to a file with rotation."""

    def configure(self) -> RotatingFileHandler:
        if not settings.LOG_FILE:
            raise ValueError("LOG_FILE must be specified for FileHandler")
        handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=self._parse_rotation_size(settings.LOG_FILE_ROTATION),
            backupCount=settings.LOG_FILE_RETENTION,
        )
        handler.setLevel(settings.LOG_LEVEL)
        formatter = CustomFormatter(LOG_FORMAT, DATE_FORMAT)
        formatter.default_msec_format = "%s.%03d"
        handler.setFormatter(formatter)
        return handler

    def _parse_rotation_size(self, size: str) -> int:
        """Converts a size string (e.g. '10MB') to bytes."""
        size = size.upper().strip()
        if size.endswith("MB"):
            return int(size[:-2]) * 1024 * 1024
        elif size.endswith("KB"):
            return int(size[:-2]) * 1024
        elif size.endswith("GB"):
            return int(size[:-2]) * 1024 * 1024 * 1024
        return int(size)


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
        logger.setLevel(settings.LOG_LEVEL)
        logger.propagate = False

        if handlers:
            for handler in handlers:
                logger.addHandler(handler.configure())

        self.loggers[name] = logger
        return logger


class RequestLogger:
    """Class for logging HTTP requests."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def get_log_level(self, status_code: int) -> int:
        """Determines the log level based on the status code."""
        if 100 <= status_code < 300:
            return logging.INFO
        elif 300 <= status_code < 400:
            return logging.DEBUG
        elif 400 <= status_code < 500:
            return logging.WARNING
        elif 500 <= status_code:
            return logging.ERROR
        return logging.INFO

    async def log_request(
        self, request: Request, response: Response, start_time: float
    ) -> None:
        """Logs information about the request."""
        try:
            latency = round(time.time() - start_time, 6)
            log_level = self.get_log_level(response.status_code)
            request_id = str(uuid.uuid4())
            response.headers["request_id"] = request_id

            log_dict = {
                "request_id": request_id,
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "latency": latency,
                "url": str(request.url),
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", ""),
                "method": request.method,
            }

            message = f"{request.method} {request.url.path} - {response.status_code}"
            if 400 <= response.status_code < 600:
                try:
                    if isinstance(response, JSONResponse):
                        body = response.body.decode("utf-8") if response.body else ""
                        log_dict["error"] = body
                except Exception as e:
                    self.logger.debug(f"Could not parse error response: {e}")

            self.logger.log(log_level, message, extra={"props": f" - {log_dict}"})

        except Exception as e:
            self.logger.error(
                f"Error while logging request: {e}",
                exc_info=True,
                extra={
                    "props": f" - {{'url': {str(request.url) if request else 'unknown'}}}"
                },
            )


logger_factory = LoggerFactory()

app_handlers = []
if settings.LOG_TO_CONSOLE:
    app_handlers.append(ConsoleHandler())
if settings.LOG_FILE:
    app_handlers.append(FileHandler())
app_logger = logger_factory.get_logger("app", handlers=app_handlers)

request_logger = RequestLogger(
    logger_factory.get_logger("requests", handlers=app_handlers)
)
