"""
LOGGING SETUP
Centralized logging configuration with rotation
"""
import logging
import sys
import io
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config.config import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Setup logger with console and file handlers
    
    Args:
        name: Logger name
        log_file: Log filename (optional, defaults to {name}.log)
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # Sanitize log records so console handlers using legacy encodings don't fail
    def _sanitize_for_console(text: str) -> str:
        try:
            return text.encode('cp1252', errors='replace').decode('cp1252')
        except Exception:
            return text.encode('utf-8', errors='replace').decode('utf-8')

    class SanitizeFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            try:
                # Convert the formatted message to a string and replace with a safe one
                msg = record.getMessage()
                record.msg = _sanitize_for_console(msg)
                record.args = ()
            except Exception:
                pass
            return True

    # Attach filter to logger so all handlers receive sanitized messages
    logger.addFilter(SanitizeFilter())
    
    # Console handler — try to reconfigure stdout to UTF-8 (Python 3.7+)
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

    class Utf8ConsoleHandler(logging.Handler):
        """Console handler that writes UTF-8 bytes to stdout.buffer."""
        terminator = "\n"
        def emit(self, record):
            try:
                msg = self.format(record) + self.terminator
                data = msg.encode('utf-8', errors='replace')
                try:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.write(b"\n") if not msg.endswith("\n") else None
                    sys.stdout.buffer.flush()
                except Exception:
                    # Fallback to text write
                    try:
                        sys.stdout.write(msg)
                        sys.stdout.write("\n") if not msg.endswith("\n") else None
                        sys.stdout.flush()
                    except Exception:
                        pass
            except Exception:
                self.handleError(record)

    console_handler = Utf8ConsoleHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file is None:
        log_file = f"{name}.log"
    
    file_path = LOG_DIR / log_file
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    # Ensure log files are written in UTF-8
    try:
        file_handler.encoding = 'utf-8'
    except Exception:
        pass
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # Prevent messages from propagating to root handlers (which may use ascii/cp1252)
    logger.propagate = False
    
    return logger
