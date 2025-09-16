"""
Performance monitoring utilities (simplified stub for streamlined UI)
This is now a minimal stub to maintain compatibility without the heavy monitoring overhead.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import contextmanager


class PerformanceMonitor:
    """Simplified performance monitor stub."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize simplified performance monitor"""
        self.db_path = db_path or "data/performance_metrics.db"

    def get_performance_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Return empty performance summary"""
        return {
            'metrics': {},
            'performance_issues': [],
            'session_count': 0,
            'total_operations': 0,
            'average_duration': 0.0
        }

    def start_session(self, session_id: str, context: Dict[str, Any] = None) -> bool:
        """Start performance session (no-op)"""
        return True

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End performance session (no-op)"""
        return {'success': True}

    def record_metric(self, name: str, value: float, unit: str = "ms", context: Dict[str, Any] = None):
        """Record performance metric (no-op)"""
        pass

    @contextmanager
    def measure_execution_time(self, operation_name: str, context: Dict[str, Any] = None):
        """Context manager for measuring execution time (no-op)"""
        start_time = datetime.now()
        try:
            yield
        finally:
            # Could log basic timing if needed
            pass

    def cleanup_old_metrics(self, days: int = 7):
        """Clean up old metrics (no-op)"""
        pass

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends (empty)"""
        return {'trends': {}, 'summary': {}}

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics (empty)"""
        return {'current_load': 0, 'active_sessions': 0}

    def start_system_monitoring(self, interval: float = 1.0):
        """Start system monitoring (no-op)"""
        pass

    def stop_system_monitoring(self):
        """Stop system monitoring (no-op)"""
        pass


# Singleton instance for easy access
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def measure_time(func):
    """Decorator for measuring function execution time (no-op)"""
    return func


class ExecutionTimer:
    """Simple execution timer stub"""

    def __init__(self, name: str = ""):
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass