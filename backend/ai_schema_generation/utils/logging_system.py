"""
T064: Comprehensive logging system for AI schema generation
Advanced logging with structured output, performance tracking, and analysis
"""

import logging
import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import queue
import atexit
from contextlib import contextmanager


class LogLevel(Enum):
    """Enhanced log levels for AI schema generation"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    PERFORMANCE = "PERFORMANCE"  # Custom level for performance metrics
    AI_ANALYSIS = "AI_ANALYSIS"  # Custom level for AI operations
    SCHEMA_EVENT = "SCHEMA_EVENT"  # Custom level for schema operations


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    document_id: Optional[str] = None
    schema_id: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    ai_metadata: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class AsyncLogHandler:
    """Asynchronous log handler for high-performance logging"""

    def __init__(self, db_path: str, max_queue_size: int = 10000):
        """Initialize async log handler"""
        self.db_path = db_path
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        self.worker_thread = None
        self.stop_event = threading.Event()
        self._setup_database()
        self._start_worker()
        atexit.register(self.shutdown)

    def _setup_database(self):
        """Setup logging database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    thread_id TEXT,
                    session_id TEXT,
                    user_id TEXT,
                    document_id TEXT,
                    schema_id TEXT,
                    performance_metrics TEXT,
                    ai_metadata TEXT,
                    extra_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON log_entries (timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON log_entries (level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_session ON log_entries (session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_schema ON log_entries (schema_id)")

    def _start_worker(self):
        """Start background worker thread"""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _worker_loop(self):
        """Background worker loop for processing log entries"""
        batch = []
        last_flush = time.time()

        while not self.stop_event.is_set():
            try:
                # Get log entry with timeout
                try:
                    entry = self.log_queue.get(timeout=1.0)
                    batch.append(entry)
                except queue.Empty:
                    pass

                # Flush batch if it's large enough or enough time has passed
                current_time = time.time()
                should_flush = (
                    len(batch) >= 100 or  # Batch size
                    (batch and current_time - last_flush > 5.0)  # Time threshold
                )

                if should_flush:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time

            except Exception as e:
                # Log to stderr if database logging fails
                print(f"Logging system error: {e}", file=sys.stderr)

        # Flush remaining entries
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[LogEntry]):
        """Flush batch of log entries to database"""
        if not batch:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                entries_data = []
                for entry in batch:
                    entries_data.append((
                        entry.timestamp,
                        entry.level,
                        entry.logger_name,
                        entry.message,
                        entry.module,
                        entry.function,
                        entry.line_number,
                        entry.thread_id,
                        entry.session_id,
                        entry.user_id,
                        entry.document_id,
                        entry.schema_id,
                        json.dumps(entry.performance_metrics) if entry.performance_metrics else None,
                        json.dumps(entry.ai_metadata) if entry.ai_metadata else None,
                        json.dumps(entry.extra_data) if entry.extra_data else None
                    ))

                conn.executemany("""
                    INSERT INTO log_entries (
                        timestamp, level, logger_name, message, module, function,
                        line_number, thread_id, session_id, user_id, document_id,
                        schema_id, performance_metrics, ai_metadata, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, entries_data)

        except Exception as e:
            print(f"Failed to flush log batch: {e}", file=sys.stderr)

    def log(self, entry: LogEntry):
        """Add log entry to queue"""
        try:
            self.log_queue.put_nowait(entry)
        except queue.Full:
            # If queue is full, drop the entry and log to stderr
            print(f"Log queue full, dropping entry: {entry.message}", file=sys.stderr)

    def shutdown(self):
        """Shutdown the async handler"""
        self.stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=10.0)


class AISchemaLogger:
    """Advanced logger for AI schema generation with structured output"""

    def __init__(self, name: str = "ai_schema_generation",
                 log_dir: str = "logs",
                 enable_console: bool = True,
                 enable_database: bool = True,
                 enable_file: bool = True):
        """Initialize AI schema logger"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.session_id = None
        self.user_id = None

        # Setup standard logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Clear existing handlers

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if enable_file:
            file_handler = logging.FileHandler(
                self.log_dir / f"{name}.log"
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

        # Database handler (async)
        if enable_database:
            self.db_handler = AsyncLogHandler(
                str(self.log_dir / f"{name}_structured.db")
            )
        else:
            self.db_handler = None

        # Performance tracking
        self.performance_contexts = {}

    def set_session_context(self, session_id: str, user_id: Optional[str] = None):
        """Set session context for all subsequent logs"""
        self.session_id = session_id
        self.user_id = user_id

    def log_structured(self, level: LogLevel, message: str,
                      document_id: Optional[str] = None,
                      schema_id: Optional[str] = None,
                      performance_metrics: Optional[Dict[str, Any]] = None,
                      ai_metadata: Optional[Dict[str, Any]] = None,
                      extra_data: Optional[Dict[str, Any]] = None):
        """Log structured entry with metadata"""
        import inspect
        import sys
        import threading

        # Get caller information
        frame = inspect.currentframe().f_back
        module = frame.f_globals.get('__name__', 'unknown')
        function = frame.f_code.co_name
        line_number = frame.f_lineno

        # Create structured log entry
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            logger_name=self.name,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            thread_id=str(threading.get_ident()),
            session_id=self.session_id,
            user_id=self.user_id,
            document_id=document_id,
            schema_id=schema_id,
            performance_metrics=performance_metrics,
            ai_metadata=ai_metadata,
            extra_data=extra_data
        )

        # Log to standard logger
        std_level = getattr(logging, level.value.split('_')[0], logging.INFO)
        self.logger.log(std_level, message)

        # Log to database if handler exists
        if self.db_handler:
            self.db_handler.log(entry)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log_structured(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log_structured(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log_structured(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log_structured(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.log_structured(LogLevel.CRITICAL, message, **kwargs)

    def performance(self, message: str, metrics: Dict[str, Any], **kwargs):
        """Log performance metrics"""
        self.log_structured(LogLevel.PERFORMANCE, message,
                          performance_metrics=metrics, **kwargs)

    def ai_analysis(self, message: str, ai_metadata: Dict[str, Any], **kwargs):
        """Log AI analysis events"""
        self.log_structured(LogLevel.AI_ANALYSIS, message,
                          ai_metadata=ai_metadata, **kwargs)

    def schema_event(self, message: str, schema_id: str, **kwargs):
        """Log schema-related events"""
        self.log_structured(LogLevel.SCHEMA_EVENT, message,
                          schema_id=schema_id, **kwargs)

    @contextmanager
    def performance_context(self, operation_name: str, **context_data):
        """Context manager for performance tracking"""
        start_time = time.time()
        context_id = f"{operation_name}_{int(start_time)}"

        self.performance_contexts[context_id] = {
            'operation': operation_name,
            'start_time': start_time,
            'context_data': context_data
        }

        try:
            self.debug(f"Starting {operation_name}", extra_data={'operation_id': context_id})
            yield context_id
        finally:
            end_time = time.time()
            duration = end_time - start_time

            metrics = {
                'operation': operation_name,
                'duration_seconds': duration,
                'start_time': start_time,
                'end_time': end_time
            }
            metrics.update(context_data)

            self.performance(f"Completed {operation_name}", metrics)

            # Clean up context
            self.performance_contexts.pop(context_id, None)

    def log_extraction_session(self, session_data: Dict[str, Any]):
        """Log complete extraction session data"""
        self.info("Extraction session completed", extra_data=session_data)

    def log_ai_generation_result(self, schema_id: str, generation_result: Dict[str, Any]):
        """Log AI schema generation result"""
        ai_metadata = {
            'model_used': generation_result.get('model_used'),
            'confidence': generation_result.get('confidence'),
            'fields_generated': generation_result.get('fields_generated'),
            'generation_time': generation_result.get('generation_time')
        }

        self.ai_analysis(
            f"AI schema generation completed for {schema_id}",
            ai_metadata=ai_metadata,
            schema_id=schema_id
        )

    def log_validation_result(self, schema_id: str, validation_result: Dict[str, Any]):
        """Log validation results"""
        self.schema_event(
            f"Schema validation completed: {validation_result.get('is_valid', False)}",
            schema_id=schema_id,
            extra_data=validation_result
        )

    def get_recent_logs(self, hours: int = 24, level: Optional[LogLevel] = None,
                       session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent log entries"""
        if not self.db_handler:
            return []

        try:
            since_time = (datetime.now() - timedelta(hours=hours)).isoformat()

            query = """
                SELECT * FROM log_entries
                WHERE timestamp > ?
            """
            params = [since_time]

            if level:
                query += " AND level = ?"
                params.append(level.value)

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            query += " ORDER BY timestamp DESC LIMIT 1000"

            with sqlite3.connect(self.db_handler.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)

                logs = []
                for row in cursor.fetchall():
                    log_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['performance_metrics', 'ai_metadata', 'extra_data']:
                        if log_dict[json_field]:
                            try:
                                log_dict[json_field] = json.loads(log_dict[json_field])
                            except json.JSONDecodeError:
                                pass
                    logs.append(log_dict)

                return logs

        except Exception as e:
            self.error(f"Failed to retrieve logs: {e}")
            return []

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary from logs"""
        perf_logs = self.get_recent_logs(hours=hours, level=LogLevel.PERFORMANCE)

        if not perf_logs:
            return {'message': 'No performance data available'}

        # Analyze performance data
        operations = {}
        total_operations = len(perf_logs)

        for log in perf_logs:
            metrics = log.get('performance_metrics', {})
            operation = metrics.get('operation', 'unknown')
            duration = metrics.get('duration_seconds', 0)

            if operation not in operations:
                operations[operation] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'durations': []
                }

            op_data = operations[operation]
            op_data['count'] += 1
            op_data['total_time'] += duration
            op_data['min_time'] = min(op_data['min_time'], duration)
            op_data['max_time'] = max(op_data['max_time'], duration)
            op_data['durations'].append(duration)

        # Calculate statistics
        summary = {
            'total_operations': total_operations,
            'time_period_hours': hours,
            'operations': {}
        }

        for operation, data in operations.items():
            avg_time = data['total_time'] / data['count']

            # Calculate median
            durations = sorted(data['durations'])
            n = len(durations)
            median_time = durations[n//2] if n % 2 else (durations[n//2-1] + durations[n//2]) / 2

            summary['operations'][operation] = {
                'count': data['count'],
                'average_time': avg_time,
                'median_time': median_time,
                'min_time': data['min_time'],
                'max_time': data['max_time'],
                'total_time': data['total_time']
            }

        return summary

    def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up old log entries"""
        if not self.db_handler:
            return 0

        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

            with sqlite3.connect(self.db_handler.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM log_entries WHERE timestamp < ?",
                    [cutoff_time]
                )
                deleted_count = cursor.rowcount

            self.info(f"Cleaned up {deleted_count} old log entries")
            return deleted_count

        except Exception as e:
            self.error(f"Failed to cleanup old logs: {e}")
            return 0


# Global logger instances
_loggers = {}

def get_logger(name: str = "ai_schema_generation") -> AISchemaLogger:
    """Get logger instance"""
    global _loggers
    if name not in _loggers:
        _loggers[name] = AISchemaLogger(name)
    return _loggers[name]


def setup_logging(name: str = "ai_schema_generation",
                 log_dir: str = "logs",
                 enable_console: bool = True,
                 enable_database: bool = True,
                 enable_file: bool = True) -> AISchemaLogger:
    """Setup and configure logging system"""
    logger = AISchemaLogger(
        name=name,
        log_dir=log_dir,
        enable_console=enable_console,
        enable_database=enable_database,
        enable_file=enable_file
    )

    global _loggers
    _loggers[name] = logger

    return logger


# Performance monitoring decorator
def log_performance(operation_name: str, logger_name: str = "ai_schema_generation"):
    """Decorator for automatic performance logging"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            with logger.performance_context(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator