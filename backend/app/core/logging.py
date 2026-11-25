"""Structured logging with sensitive data redaction."""
import logging
import re

SENSITIVE_PATTERNS = [
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[REDACTED_PAN]"),
    (re.compile(r"(?i)(api[_-]?key|authorization|bearer|secret|password)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in SENSITIVE_PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        return True


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("cardguard")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


logger = configure_logging()
