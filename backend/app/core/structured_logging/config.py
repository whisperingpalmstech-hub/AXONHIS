import logging
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Context variables for correlation tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)


class StructuredLogger:
    """Structured logger with correlation ID support for distributed tracing."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _get_context(self) -> Dict[str, Any]:
        """Get current context variables."""
        return {
            "correlation_id": correlation_id_var.get(),
            "request_id": request_id_var.get(),
            "user_id": user_id_var.get(),
            "tenant_id": tenant_id_var.get(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _log(self, level: str, message: str, **kwargs):
        """Log with structured context."""
        context = self._get_context()
        log_data = {
            "message": message,
            "level": level,
            **context,
            **kwargs
        }
        
        log_str = json.dumps(log_data, default=str)
        
        if level == "DEBUG":
            self.logger.debug(log_str)
        elif level == "INFO":
            self.logger.info(log_str)
        elif level == "WARNING":
            self.logger.warning(log_str)
        elif level == "ERROR":
            self.logger.error(log_str)
        elif level == "CRITICAL":
            self.logger.critical(log_str)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log("CRITICAL", message, **kwargs)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    return StructuredLogger(name)


def set_correlation_id(correlation_id: Optional[str] = None):
    """Set correlation ID for current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def set_request_id(request_id: Optional[str] = None):
    """Set request ID for current context."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get current request ID."""
    return request_id_var.get()


def set_user_id(user_id: str):
    """Set user ID for current context."""
    user_id_var.set(user_id)


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return user_id_var.get()


def set_tenant_id(tenant_id: str):
    """Set tenant ID for current context."""
    tenant_id_var.set(tenant_id)


def get_tenant_id() -> Optional[str]:
    """Get current tenant ID."""
    return tenant_id_var.get()


def clear_context():
    """Clear all context variables."""
    correlation_id_var.set(None)
    request_id_var.set(None)
    user_id_var.set(None)
    tenant_id_var.set(None)
