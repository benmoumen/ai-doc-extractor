"""
Performance Optimizer for Schema Management System

Implements caching, debouncing, lazy loading, and other performance optimizations
to ensure responsive UI interactions and efficient resource usage.
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List, Set
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import streamlit as st
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import weakref

from .models.schema import Schema
from .services.schema_service import SchemaService


class DebounceManager:
    """
    Manages debounced function calls to prevent excessive API calls or updates.
    """
    
    def __init__(self):
        self._pending_calls: Dict[str, threading.Timer] = {}
        self._lock = threading.RLock()
    
    def debounce(self, delay: float, key: Optional[str] = None):
        """
        Decorator to debounce function calls.
        
        Args:
            delay: Delay in seconds before executing the function
            key: Optional key to group debounced calls
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                call_key = key or f"{func.__name__}_{id(func)}"
                
                with self._lock:
                    # Cancel existing pending call
                    if call_key in self._pending_calls:
                        self._pending_calls[call_key].cancel()
                    
                    # Schedule new call
                    timer = threading.Timer(
                        delay,
                        lambda: self._execute_call(func, args, kwargs, call_key)
                    )
                    self._pending_calls[call_key] = timer
                    timer.start()
            
            return wrapper
        return decorator
    
    def _execute_call(self, func: Callable, args: tuple, kwargs: dict, key: str):
        """Execute the debounced function call."""
        try:
            func(*args, **kwargs)
        except Exception as e:
            # Log error but don't propagate to avoid breaking the app
            st.error(f"Debounced function error: {str(e)}")
        finally:
            with self._lock:
                if key in self._pending_calls:
                    del self._pending_calls[key]
    
    def cancel_all(self):
        """Cancel all pending debounced calls."""
        with self._lock:
            for timer in self._pending_calls.values():
                timer.cancel()
            self._pending_calls.clear()


class CacheManager:
    """
    Manages various caches for schema management system.
    """
    
    def __init__(self, max_size: int = 128, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._remove_key(key)
                return None
            
            # Update access time
            self._access_times[key] = datetime.now()
            return self._cache[key]['value']
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            # Evict expired entries
            self._evict_expired()
            
            # Evict LRU if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Store value
            self._cache[key] = {
                'value': value,
                'created': datetime.now()
            }
            self._access_times[key] = datetime.now()
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self._cache:
            return True
        
        created = self._cache[key]['created']
        return (datetime.now() - created).total_seconds() > self.ttl
    
    def _evict_expired(self):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key in self._cache.keys()
            if self._is_expired(key)
        ]
        for key in expired_keys:
            self._remove_key(key)
    
    def _evict_lru(self):
        """Remove least recently used entry."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._remove_key(lru_key)
    
    def _remove_key(self, key: str):
        """Remove key from cache and access times."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(1 for key in self._cache.keys() if self._is_expired(key))
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_count,
                'expired_entries': expired_count,
                'max_size': self.max_size,
                'ttl_seconds': self.ttl,
                'hit_ratio': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
            }


class LazyLoader:
    """
    Implements lazy loading for expensive operations.
    """
    
    def __init__(self):
        self._loaded: Set[str] = set()
        self._loading: Set[str] = set()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
    
    def load_async(
        self,
        key: str,
        loader_func: Callable,
        callback: Optional[Callable] = None,
        force_reload: bool = False
    ) -> bool:
        """
        Load data asynchronously.
        
        Args:
            key: Unique key for the load operation
            loader_func: Function to load the data
            callback: Callback to execute when loading completes
            force_reload: Force reload even if already loaded
            
        Returns:
            True if loading started, False if already loaded/loading
        """
        with self._lock:
            if not force_reload and (key in self._loaded or key in self._loading):
                return False
            
            if key in self._loaded and force_reload:
                self._loaded.remove(key)
            
            if key not in self._loading:
                self._loading.add(key)
                
                if callback:
                    if key not in self._callbacks:
                        self._callbacks[key] = []
                    self._callbacks[key].append(callback)
                
                # Submit async load
                future = self._executor.submit(self._load_data, key, loader_func)
                return True
            
            return False
    
    def _load_data(self, key: str, loader_func: Callable):
        """Execute the data loading operation."""
        try:
            result = loader_func()
            
            with self._lock:
                self._loading.discard(key)
                self._loaded.add(key)
                
                # Execute callbacks
                callbacks = self._callbacks.get(key, [])
                for callback in callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        st.error(f"Lazy load callback error: {str(e)}")
                
                # Clean up callbacks
                if key in self._callbacks:
                    del self._callbacks[key]
                    
        except Exception as e:
            with self._lock:
                self._loading.discard(key)
            st.error(f"Lazy load error for {key}: {str(e)}")
    
    def is_loaded(self, key: str) -> bool:
        """Check if data is loaded."""
        return key in self._loaded
    
    def is_loading(self, key: str) -> bool:
        """Check if data is currently loading."""
        return key in self._loading


class PerformanceOptimizer:
    """
    Main performance optimizer that coordinates all optimization strategies.
    """
    
    def __init__(self):
        self.debounce_manager = DebounceManager()
        self.cache_manager = CacheManager(max_size=256, ttl=600)  # 10 minutes TTL
        self.lazy_loader = LazyLoader()
        self.schema_cache = CacheManager(max_size=64, ttl=300)  # 5 minutes for schemas
        self._metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'debounced_calls': 0,
            'lazy_loads': 0
        }
    
    def get_cached_schema_list(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached schema list."""
        cached = self.cache_manager.get('schema_list')
        if cached:
            self._metrics['cache_hits'] += 1
            return cached
        
        self._metrics['cache_misses'] += 1
        return None
    
    def cache_schema_list(self, schema_list: List[Dict[str, Any]]):
        """Cache schema list."""
        self.cache_manager.set('schema_list', schema_list)
    
    def get_cached_schema(self, schema_id: str) -> Optional[Schema]:
        """Get cached schema by ID."""
        cache_key = f"schema_{schema_id}"
        cached = self.schema_cache.get(cache_key)
        if cached:
            self._metrics['cache_hits'] += 1
            return cached
        
        self._metrics['cache_misses'] += 1
        return None
    
    def cache_schema(self, schema: Schema):
        """Cache a schema."""
        cache_key = f"schema_{schema.id}"
        self.schema_cache.set(cache_key, schema)
    
    def debounced_save_schema(self, delay: float = 2.0):
        """Decorator for debounced schema saving."""
        self._metrics['debounced_calls'] += 1
        return self.debounce_manager.debounce(delay, 'save_schema')
    
    def debounced_validation(self, delay: float = 1.0):
        """Decorator for debounced validation."""
        self._metrics['debounced_calls'] += 1
        return self.debounce_manager.debounce(delay, 'validation')
    
    def preload_schema_templates(self):
        """Preload schema templates asynchronously."""
        if not self.lazy_loader.is_loaded('templates'):
            self._metrics['lazy_loads'] += 1
            
            def load_templates():
                # Import here to avoid circular imports
                from .services.template_service import template_service
                return template_service.get_all_templates()
            
            self.lazy_loader.load_async(
                'templates',
                load_templates,
                callback=lambda templates: self.cache_manager.set('templates', templates)
            )
    
    def preload_schema_validation_rules(self):
        """Preload validation rules asynchronously."""
        if not self.lazy_loader.is_loaded('validation_rules'):
            self._metrics['lazy_loads'] += 1
            
            def load_rules():
                # Common validation rules that can be precomputed
                return {
                    'common_patterns': {
                        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                        'phone': r'^\+?1?\d{9,15}$',
                        'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
                    },
                    'field_types': ['string', 'number', 'integer', 'boolean', 'date', 'datetime', 'email', 'url', 'phone', 'select', 'multiselect']
                }
            
            self.lazy_loader.load_async('validation_rules', load_rules)
    
    def get_schema_hash(self, schema_data: Dict[str, Any]) -> str:
        """Generate hash for schema data to detect changes."""
        # Create a stable hash of the schema data
        schema_json = json.dumps(schema_data, sort_keys=True, ensure_ascii=True)
        return hashlib.md5(schema_json.encode()).hexdigest()
    
    def should_update_ui(self, current_hash: str, previous_hash: Optional[str]) -> bool:
        """Check if UI should be updated based on data changes."""
        return current_hash != previous_hash
    
    def optimize_field_list_rendering(self, fields: List[Dict[str, Any]], max_visible: int = 50) -> Dict[str, Any]:
        """
        Optimize field list rendering for large schemas.
        
        Args:
            fields: List of field data
            max_visible: Maximum number of fields to render at once
            
        Returns:
            Optimized rendering configuration
        """
        total_fields = len(fields)
        
        if total_fields <= max_visible:
            return {
                'use_pagination': False,
                'visible_fields': fields,
                'total_pages': 1,
                'current_page': 1
            }
        
        # Use session state to track current page
        page_key = 'field_list_page'
        current_page = st.session_state.get(page_key, 1)
        total_pages = (total_fields + max_visible - 1) // max_visible
        
        # Ensure current page is valid
        current_page = max(1, min(current_page, total_pages))
        st.session_state[page_key] = current_page
        
        # Calculate visible fields
        start_idx = (current_page - 1) * max_visible
        end_idx = min(start_idx + max_visible, total_fields)
        visible_fields = fields[start_idx:end_idx]
        
        return {
            'use_pagination': True,
            'visible_fields': visible_fields,
            'total_pages': total_pages,
            'current_page': current_page,
            'total_fields': total_fields,
            'start_idx': start_idx + 1,
            'end_idx': end_idx
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        cache_stats = self.cache_manager.stats()
        schema_cache_stats = self.schema_cache.stats()
        
        return {
            'cache_metrics': cache_stats,
            'schema_cache_metrics': schema_cache_stats,
            'operation_metrics': self._metrics.copy(),
            'lazy_load_status': {
                'templates_loaded': self.lazy_loader.is_loaded('templates'),
                'validation_rules_loaded': self.lazy_loader.is_loaded('validation_rules'),
                'active_loads': len(self.lazy_loader._loading)
            }
        }
    
    def clear_caches(self):
        """Clear all caches."""
        self.cache_manager.clear()
        self.schema_cache.clear()
    
    def shutdown(self):
        """Shutdown the performance optimizer."""
        self.debounce_manager.cancel_all()
        self.lazy_loader._executor.shutdown(wait=True)


# Global optimizer instance
performance_optimizer = PerformanceOptimizer()


# Convenience functions and decorators

def cached_schema_operation(func: Callable) -> Callable:
    """Decorator to cache schema operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
        
        # Try to get from cache
        cached_result = performance_optimizer.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute function and cache result
        result = func(*args, **kwargs)
        performance_optimizer.cache_manager.set(cache_key, result)
        return result
    
    return wrapper


def debounced_update(delay: float = 1.0, key: Optional[str] = None):
    """Decorator for debounced UI updates."""
    return performance_optimizer.debounce_manager.debounce(delay, key)


@lru_cache(maxsize=128)
def get_field_type_options() -> List[str]:
    """Get cached field type options."""
    return ['string', 'number', 'integer', 'boolean', 'date', 'datetime', 
            'email', 'url', 'phone', 'select', 'multiselect', 'file']


@lru_cache(maxsize=64)
def get_validation_rule_types() -> List[str]:
    """Get cached validation rule types."""
    return ['required', 'min_length', 'max_length', 'regex', 'min_value', 
            'max_value', 'email_format', 'phone_format', 'date_format']


def optimize_large_schema_rendering(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize rendering for large schemas.
    
    Args:
        schema_data: Schema data to optimize
        
    Returns:
        Optimized configuration for rendering
    """
    fields = schema_data.get('fields', [])
    field_count = len(fields)
    
    # Use different strategies based on field count
    if field_count <= 20:
        return {'strategy': 'full_render', 'data': schema_data}
    
    elif field_count <= 100:
        # Use pagination for medium schemas
        return {
            'strategy': 'paginated',
            'data': schema_data,
            'pagination': performance_optimizer.optimize_field_list_rendering(fields, max_visible=25)
        }
    
    else:
        # Use virtual scrolling for large schemas
        return {
            'strategy': 'virtual_scroll',
            'data': schema_data,
            'pagination': performance_optimizer.optimize_field_list_rendering(fields, max_visible=50),
            'lazy_load_threshold': 10
        }


def preload_common_data():
    """Preload commonly used data."""
    performance_optimizer.preload_schema_templates()
    performance_optimizer.preload_schema_validation_rules()


def get_optimization_status() -> Dict[str, Any]:
    """Get current optimization status."""
    return performance_optimizer.get_performance_metrics()


def clear_optimization_caches():
    """Clear all optimization caches."""
    performance_optimizer.clear_caches()


# Context manager for performance monitoring
class PerformanceMonitor:
    """Context manager to monitor performance of operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Store performance data in session state
            perf_key = 'performance_data'
            if perf_key not in st.session_state:
                st.session_state[perf_key] = {}
            
            st.session_state[perf_key][self.operation_name] = {
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'success': exc_type is None
            }