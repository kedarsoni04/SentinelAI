import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable to correlate log lines with individual HTTP requests
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

# Regex to mask passwords, authorization headers, and tokens in log strings
SENSITIVE_PATTERNS = [
    (re.compile(r'("?(?:password|token|secret|api_key|access_token)"?\s*[:=]\s*)"([^"]+)"', re.IGNORECASE), r'\1"***"'),
    (re.compile(r'("?(?:password|token|secret|api_key|access_token)"?\s*[:=]\s*)\'([^\']+)\'', re.IGNORECASE), r"\1'***'"),
    (re.compile(r'Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*', re.IGNORECASE), r'Bearer ***'),
    (re.compile(r'://([^:@]+):([^@]+)@', re.IGNORECASE), r'://\1:***@'),
]


def mask_sensitive_text(message: str) -> str:
    """Mask credentials, tokens, and secrets from log strings."""
    if not isinstance(message, str):
        return str(message)
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class StructuredJSONFormatter(logging.Formatter):
    """
    Production-ready JSON log formatter.
    Outputs structured JSON lines compatible with Datadog, CloudWatch, GCP Cloud Logging, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "sentinelai-backend",
            "logger": record.name,
            "message": mask_sensitive_text(record.getMessage()),
        }

        if req_id:
            log_entry["request_id"] = req_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include custom extra attributes if provided
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message"
            } and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry)


class DevConsoleFormatter(logging.Formatter):
    """Human-readable console log formatter for local development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        req_str = f"[{req_id[:8]}] " if req_id else ""
        time_str = datetime.now().strftime("%H:%M:%S")
        msg = mask_sensitive_text(record.getMessage())
        formatted = f"{time_str} {record.levelname:<7} {req_str}[{record.name}] {msg}"
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted


def setup_logging(is_production: bool = False, log_level: str = "INFO") -> None:
    """
    Configure root application logging.
    Uses JSON formatting in production and readable console formatting in development.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if is_production:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(DevConsoleFormatter())

    root_logger.addHandler(handler)

    # Quiet overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
