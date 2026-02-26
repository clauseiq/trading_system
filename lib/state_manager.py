"""
STATE MANAGER
Thread-safe state persistence with file locking
"""
import json
import time
try:
    import fcntl  # Unix
    _HAS_FCNTL = True
except Exception:
    _HAS_FCNTL = False
    import msvcrt  # Windows fallback
import logging
from pathlib import Path
from typing import Any, Dict
from contextlib import contextmanager

log = logging.getLogger(__name__)


class StateManager:
    """Thread-safe JSON state manager with file locking"""
    
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
    @contextmanager
    def _lock(self, mode='r'):
        """File lock context manager"""
        lockfile = self.filepath.with_suffix('.lock')
        lock_fd = None
        try:
            # Use append mode so we don't truncate the file (safer cross-platform)
            lock_fd = open(lockfile, 'a+')
            if _HAS_FCNTL:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
            else:
                # msvcrt.locking locks a byte range; lock 1 byte from start
                try:
                    lock_fd.seek(0)
                except Exception:
                    pass
                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
            yield
        finally:
            if lock_fd:
                if _HAS_FCNTL:
                    try:
                        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
                else:
                    try:
                        lock_fd.seek(0)
                    except Exception:
                        pass
                    try:
                        msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                lock_fd.close()
    
    def load(self, default: Dict = None) -> Dict:
        """Load state with locking"""
        with self._lock('r'):
            if not self.filepath.exists():
                return default or {}
            
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                log.error(f"Corrupted state file {self.filepath}: {e}")
                # Backup corrupted file
                backup = self.filepath.with_suffix('.corrupted')
                self.filepath.rename(backup)
                log.info(f"Backed up to {backup}")
                return default or {}
            except Exception as e:
                log.error(f"Failed to load {self.filepath}: {e}")
                return default or {}
    
    def save(self, data: Dict):
        """Save state with locking and atomic write"""
        with self._lock('w'):
            # Atomic write: write to temp, then rename
            temp_file = self.filepath.with_suffix('.tmp')
            try:
                with open(temp_file, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                temp_file.replace(self.filepath)
            except Exception as e:
                log.error(f"Failed to save {self.filepath}: {e}")
                if temp_file.exists():
                    temp_file.unlink()
                raise
    
    def update(self, updates: Dict):
        """Update specific fields atomically"""
        with self._lock('w'):
            data = self.load()
            data.update(updates)
            self.save(data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get specific field"""
        data = self.load()
        return data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set specific field"""
        self.update({key: value})
