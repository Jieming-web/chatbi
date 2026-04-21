import contextvars
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional


_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")


def new_trace_id() -> str:
    tid = uuid.uuid4().hex[:12]
    _trace_id.set(tid)
    return tid


def get_trace_id() -> str:
    return _trace_id.get()


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "trace_id": get_trace_id(),
            "logger": record.name,
        }
        if isinstance(record.msg, dict):
            payload.update(record.msg)
        else:
            payload["message"] = record.getMessage()
        return json.dumps(payload, ensure_ascii=False)


def get_audit_logger(log_path: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("chatbi.audit")
    if getattr(logger, "_chatbi_configured", False):
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if log_path is None:
        log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "chatbi_audit.log",
        )
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(_JsonFormatter())
    logger.addHandler(handler)
    logger._chatbi_configured = True  # type: ignore[attr-defined]
    return logger


def audit(record: dict) -> None:
    get_audit_logger().info(record)
