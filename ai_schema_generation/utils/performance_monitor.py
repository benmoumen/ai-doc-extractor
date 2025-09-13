"""
T058: Performance monitoring utilities
Comprehensive performance tracking for AI schema generation pipeline
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import sqlite3
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSession:
    """Performance monitoring session"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: List[PerformanceMetric] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Comprehensive performance monitoring system for AI schema generation."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize performance monitor"""
        self.db_path = db_path or "data/performance_metrics.db"
        self.current_session: Optional[PerformanceSession] = None
        self.metrics_buffer: deque = deque(maxlen=1000)
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Performance thresholds (in seconds)
        self.thresholds = {
            'document_processing': 5.0,
            'ai_analysis': 60.0,
            'field_enhancement': 10.0,
            'validation_inference': 5.0,
            'schema_generation': 10.0,
            'confidence_analysis': 5.0,
            'total_pipeline': 120.0
        }

        self._setup_database()

    def _setup_database(self):
        """Setup performance metrics database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES performance_sessions (session_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_session_name
                ON performance_metrics (session_id, metric_name)
            """)

    def start_session(self, session_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Start a new performance monitoring session"""
        self.current_session = PerformanceSession(
            session_id=session_id,
            start_time=datetime.now(),
            context=context or {}
        )

        # Save session to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_sessions (session_id, start_time, context)
                VALUES (?, ?, ?)
            """, (
                session_id,
                self.current_session.start_time.isoformat(),
                json.dumps(context or {})
            ))

        return session_id

    def end_session(self) -> Optional[PerformanceSession]:
        """End current performance monitoring session"""
        if not self.current_session:
            return None

        self.current_session.end_time = datetime.now()

        # Update session in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE performance_sessions
                SET end_time = ?
                WHERE session_id = ?
            """, (
                self.current_session.end_time.isoformat(),
                self.current_session.session_id
            ))

        completed_session = self.current_session
        self.current_session = None
        return completed_session

    def record_metric(self, name: str, value: float, unit: str = 'seconds',
                     context: Optional[Dict[str, Any]] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {}
        )

        # Add to current session if active
        if self.current_session:
            self.current_session.metrics.append(metric)
            session_id = self.current_session.session_id
        else:
            session_id = None

        # Add to buffer
        self.metrics_buffer.append(metric)

        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics
                (session_id, metric_name, metric_value, metric_unit, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                name,
                value,
                unit,
                metric.timestamp.isoformat(),
                json.dumps(context or {})
            ))

    def measure_execution_time(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """Decorator/context manager for measuring execution time"""
        return ExecutionTimer(self, operation_name, context)

    def start_system_monitoring(self, interval: float = 1.0):
        """Start continuous system resource monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()

    def stop_system_monitoring(self):
        """Stop continuous system resource monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)

    def _monitor_system_resources(self, interval: float):
        """Monitor system resources in background thread"""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.record_metric('cpu_usage', cpu_percent, 'percent')

                # Memory usage
                memory = psutil.virtual_memory()
                self.record_metric('memory_usage', memory.percent, 'percent')
                self.record_metric('memory_available', memory.available / (1024**3), 'GB')

                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.record_metric('disk_read_mb', disk_io.read_bytes / (1024**2), 'MB')
                    self.record_metric('disk_write_mb', disk_io.write_bytes / (1024**2), 'MB')

                time.sleep(interval)

            except Exception:
                # Continue monitoring even if individual measurements fail
                time.sleep(interval)

    def get_performance_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for session or overall"""
        with sqlite3.connect(self.db_path) as conn:
            if session_id:
                # Session-specific summary
                cursor = conn.execute("""
                    SELECT metric_name, AVG(metric_value), MIN(metric_value),
                           MAX(metric_value), COUNT(*), metric_unit
                    FROM performance_metrics
                    WHERE session_id = ?
                    GROUP BY metric_name, metric_unit
                """, (session_id,))
            else:
                # Overall summary
                cursor = conn.execute("""
                    SELECT metric_name, AVG(metric_value), MIN(metric_value),
                           MAX(metric_value), COUNT(*), metric_unit
                    FROM performance_metrics
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY metric_name, metric_unit
                """)

            metrics_summary = {}
            for row in cursor.fetchall():
                metric_name, avg_val, min_val, max_val, count, unit = row
                metrics_summary[metric_name] = {
                    'average': avg_val,
                    'minimum': min_val,
                    'maximum': max_val,
                    'count': count,
                    'unit': unit
                }

        return {
            'session_id': session_id,
            'metrics': metrics_summary,
            'thresholds': self.thresholds,
            'performance_issues': self._identify_performance_issues(metrics_summary)
        }

    def _identify_performance_issues(self, metrics_summary: Dict[str, Any]) -> List[str]:
        """Identify performance issues based on metrics"""
        issues = []

        for metric_name, stats in metrics_summary.items():
            if metric_name in self.thresholds:
                threshold = self.thresholds[metric_name]
                if stats['average'] > threshold:
                    issues.append(f"{metric_name} averaging {stats['average']:.2f}s (threshold: {threshold}s)")
                if stats['maximum'] > threshold * 2:
                    issues.append(f"{metric_name} peak {stats['maximum']:.2f}s (critical)")

        # Check system resource issues
        if 'cpu_usage' in metrics_summary and metrics_summary['cpu_usage']['average'] > 80:
            issues.append(f"High CPU usage: {metrics_summary['cpu_usage']['average']:.1f}%")

        if 'memory_usage' in metrics_summary and metrics_summary['memory_usage']['average'] > 85:
            issues.append(f"High memory usage: {metrics_summary['memory_usage']['average']:.1f}%")

        return issues

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over time"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(timestamp) as date, metric_name,
                       AVG(metric_value) as avg_value, COUNT(*) as count
                FROM performance_metrics
                WHERE timestamp > datetime('now', '-{} days')
                GROUP BY DATE(timestamp), metric_name
                ORDER BY date DESC, metric_name
            """.format(days))

            trends = defaultdict(list)
            for row in cursor.fetchall():
                date, metric_name, avg_value, count = row
                trends[metric_name].append({
                    'date': date,
                    'value': avg_value,
                    'count': count
                })

        return dict(trends)

    def export_metrics(self, session_id: Optional[str] = None, format: str = 'json') -> str:
        """Export performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            if session_id:
                cursor = conn.execute("""
                    SELECT * FROM performance_metrics
                    WHERE session_id = ?
                    ORDER BY timestamp
                """, (session_id,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM performance_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)

            columns = [description[0] for description in cursor.description]
            metrics_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if format == 'json':
            return json.dumps(metrics_data, indent=2, default=str)
        elif format == 'csv':
            # Simple CSV export
            if not metrics_data:
                return ""

            csv_lines = [','.join(columns)]
            for row in metrics_data:
                csv_lines.append(','.join(str(row[col]) for col in columns))
            return '\n'.join(csv_lines)

        return str(metrics_data)

    def cleanup_old_metrics(self, days: int = 30) -> int:
        """Clean up old performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM performance_metrics
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))

            deleted_metrics = cursor.rowcount

            # Also clean up orphaned sessions
            cursor = conn.execute("""
                DELETE FROM performance_sessions
                WHERE session_id NOT IN (
                    SELECT DISTINCT session_id FROM performance_metrics
                    WHERE session_id IS NOT NULL
                )
            """)

            return deleted_metrics

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        current_metrics = {}

        # Get latest metrics from buffer
        recent_metrics = list(self.metrics_buffer)[-10:]  # Last 10 metrics

        for metric in recent_metrics:
            current_metrics[metric.name] = {
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat()
            }

        # Add current system metrics
        try:
            current_metrics['current_cpu'] = {
                'value': psutil.cpu_percent(interval=0.1),
                'unit': 'percent',
                'timestamp': datetime.now().isoformat()
            }

            memory = psutil.virtual_memory()
            current_metrics['current_memory'] = {
                'value': memory.percent,
                'unit': 'percent',
                'timestamp': datetime.now().isoformat()
            }
        except Exception:
            pass

        return current_metrics


class ExecutionTimer:
    """Context manager for measuring execution time"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str,
                 context: Optional[Dict[str, Any]] = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.context = context or {}
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time

        # Add exception info to context if there was an error
        if exc_type:
            self.context['error'] = True
            self.context['exception_type'] = exc_type.__name__

        self.monitor.record_metric(
            self.operation_name,
            execution_time,
            'seconds',
            self.context
        )

    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed time so far"""
        if self.start_time:
            return time.time() - self.start_time
        return None


# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get singleton performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def measure_time(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """Decorator for measuring function execution time"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.measure_execution_time(operation_name, context):
                return func(*args, **kwargs)
        return wrapper
    return decorator