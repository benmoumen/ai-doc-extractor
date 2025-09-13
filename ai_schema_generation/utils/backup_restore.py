"""
T065: Backup and restore utilities for AI schema generation
Comprehensive backup, restore, and data migration system
"""

import json
import zipfile
import shutil
import sqlite3
import pickle
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class BackupType(Enum):
    """Types of backup operations"""
    FULL = "full"           # Complete system backup
    SCHEMAS = "schemas"     # Schema definitions only
    DATA = "data"          # Extracted data only
    CACHE = "cache"        # Cache data only
    LOGS = "logs"          # Log data only
    INCREMENTAL = "incremental"  # Changes since last backup


class RestoreMode(Enum):
    """Restore operation modes"""
    REPLACE = "replace"     # Replace existing data
    MERGE = "merge"        # Merge with existing data
    SKIP_EXISTING = "skip_existing"  # Skip if data exists


@dataclass
class BackupManifest:
    """Backup manifest with metadata"""
    backup_id: str
    backup_type: BackupType
    created_at: str
    version: str
    description: str
    file_count: int
    total_size_bytes: int
    checksum: str
    components: List[str]
    metadata: Dict[str, Any]


class BackupManager:
    """Comprehensive backup and restore system"""

    def __init__(self, backup_dir: str = "backups", data_dir: str = "data"):
        """Initialize backup manager"""
        self.backup_dir = Path(backup_dir)
        self.data_dir = Path(data_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup registry database
        self.registry_db = self.backup_dir / "backup_registry.db"
        self._setup_registry()

        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Compression settings
        self.compression_level = 6

    def _setup_registry(self):
        """Setup backup registry database"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    version TEXT,
                    description TEXT,
                    file_count INTEGER,
                    total_size_bytes INTEGER,
                    checksum TEXT,
                    components TEXT,
                    metadata TEXT,
                    file_path TEXT,
                    restored_count INTEGER DEFAULT 0,
                    last_restored TEXT,
                    is_valid BOOLEAN DEFAULT 1
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_created
                ON backups (created_at DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_type
                ON backups (backup_type)
            """)

    def create_backup(self, backup_type: BackupType = BackupType.FULL,
                     description: str = None,
                     include_components: Optional[List[str]] = None,
                     exclude_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create backup of specified type

        Args:
            backup_type: Type of backup to create
            description: Optional description
            include_components: Specific components to include
            exclude_components: Components to exclude

        Returns:
            Dictionary with backup result information
        """
        backup_id = self._generate_backup_id(backup_type)
        timestamp = datetime.now().isoformat()

        try:
            # Determine components to backup
            components = self._determine_backup_components(
                backup_type, include_components, exclude_components
            )

            # Create backup directory
            backup_path = self.backup_dir / f"{backup_id}.zip"

            # Perform backup
            manifest = self._perform_backup(
                backup_id, backup_type, components, backup_path, description
            )

            # Register backup
            self._register_backup(manifest, backup_path)

            return {
                'success': True,
                'backup_id': backup_id,
                'backup_path': str(backup_path),
                'manifest': asdict(manifest),
                'message': f'{backup_type.value.title()} backup created successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'backup_id': backup_id,
                'message': f'Failed to create {backup_type.value} backup'
            }

    def _generate_backup_id(self, backup_type: BackupType) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        type_prefix = backup_type.value[:4].upper()
        return f"{type_prefix}_{timestamp}"

    def _determine_backup_components(self, backup_type: BackupType,
                                   include_components: Optional[List[str]] = None,
                                   exclude_components: Optional[List[str]] = None) -> List[str]:
        """Determine which components to include in backup"""
        all_components = [
            'schemas',
            'extracted_data',
            'cache',
            'logs',
            'performance_metrics',
            'validation_results',
            'ai_metadata'
        ]

        if backup_type == BackupType.FULL:
            components = all_components.copy()
        elif backup_type == BackupType.SCHEMAS:
            components = ['schemas', 'ai_metadata']
        elif backup_type == BackupType.DATA:
            components = ['extracted_data', 'validation_results']
        elif backup_type == BackupType.CACHE:
            components = ['cache']
        elif backup_type == BackupType.LOGS:
            components = ['logs', 'performance_metrics']
        elif backup_type == BackupType.INCREMENTAL:
            components = self._get_incremental_components()
        else:
            components = all_components.copy()

        # Apply include/exclude filters
        if include_components:
            components = [c for c in components if c in include_components]

        if exclude_components:
            components = [c for c in components if c not in exclude_components]

        return components

    def _get_incremental_components(self) -> List[str]:
        """Determine components for incremental backup"""
        # For incremental, include components with recent changes
        # This is a simplified implementation
        return ['schemas', 'extracted_data', 'ai_metadata']

    def _perform_backup(self, backup_id: str, backup_type: BackupType,
                       components: List[str], backup_path: Path,
                       description: str = None) -> BackupManifest:
        """Perform the actual backup operation"""
        start_time = time.time()
        total_size = 0
        file_count = 0
        component_results = {}

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED,
                            compresslevel=self.compression_level) as zip_file:

            # Add manifest placeholder
            manifest_data = {
                'backup_id': backup_id,
                'backup_type': backup_type.value,
                'created_at': datetime.now().isoformat(),
                'components': components
            }
            zip_file.writestr('manifest.json', json.dumps(manifest_data, indent=2))

            # Backup each component in parallel
            futures = {}
            for component in components:
                future = self.executor.submit(self._backup_component, component)
                futures[future] = component

            # Collect results and add to zip
            for future in as_completed(futures):
                component = futures[future]
                try:
                    component_data = future.result()
                    if component_data:
                        # Add component data to zip
                        component_path = f"components/{component}.json"
                        zip_file.writestr(component_path, json.dumps(component_data, indent=2))

                        component_results[component] = {
                            'status': 'success',
                            'file_count': len(component_data) if isinstance(component_data, list) else 1,
                            'size_bytes': len(json.dumps(component_data))
                        }
                        file_count += component_results[component]['file_count']
                        total_size += component_results[component]['size_bytes']

                except Exception as e:
                    component_results[component] = {
                        'status': 'error',
                        'error': str(e),
                        'file_count': 0,
                        'size_bytes': 0
                    }

        # Calculate checksum
        checksum = self._calculate_file_checksum(backup_path)

        # Create final manifest
        manifest = BackupManifest(
            backup_id=backup_id,
            backup_type=backup_type,
            created_at=datetime.now().isoformat(),
            version="1.0",
            description=description or f"Automated {backup_type.value} backup",
            file_count=file_count,
            total_size_bytes=total_size,
            checksum=checksum,
            components=components,
            metadata={
                'duration_seconds': time.time() - start_time,
                'component_results': component_results,
                'compression_ratio': total_size / backup_path.stat().st_size if total_size > 0 else 1.0
            }
        )

        return manifest

    def _backup_component(self, component: str) -> Optional[Dict[str, Any]]:
        """Backup a specific component"""
        try:
            if component == 'schemas':
                return self._backup_schemas()
            elif component == 'extracted_data':
                return self._backup_extracted_data()
            elif component == 'cache':
                return self._backup_cache()
            elif component == 'logs':
                return self._backup_logs()
            elif component == 'performance_metrics':
                return self._backup_performance_metrics()
            elif component == 'validation_results':
                return self._backup_validation_results()
            elif component == 'ai_metadata':
                return self._backup_ai_metadata()
            else:
                return None

        except Exception as e:
            raise Exception(f"Failed to backup {component}: {e}")

    def _backup_schemas(self) -> Dict[str, Any]:
        """Backup schema definitions"""
        schemas = {}

        # Backup from schema management directory
        schema_dir = self.data_dir / "schemas"
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.json"):
                try:
                    with open(schema_file, 'r') as f:
                        schema_data = json.load(f)
                        schemas[schema_file.stem] = schema_data
                except Exception as e:
                    schemas[f"error_{schema_file.stem}"] = {'error': str(e)}

        return {'schemas': schemas, 'count': len(schemas)}

    def _backup_extracted_data(self) -> Dict[str, Any]:
        """Backup extracted data"""
        data = {}

        # Backup from extraction results directory
        data_dir = self.data_dir / "extractions"
        if data_dir.exists():
            for data_file in data_dir.glob("*.json"):
                try:
                    with open(data_file, 'r') as f:
                        extraction_data = json.load(f)
                        data[data_file.stem] = extraction_data
                except Exception as e:
                    data[f"error_{data_file.stem}"] = {'error': str(e)}

        return {'extracted_data': data, 'count': len(data)}

    def _backup_cache(self) -> Dict[str, Any]:
        """Backup cache data"""
        cache_data = {}

        # Backup cache database
        cache_db = self.data_dir / "cache" / "cache.db"
        if cache_db.exists():
            try:
                with sqlite3.connect(cache_db) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("SELECT * FROM cache_entries")

                    entries = []
                    for row in cursor.fetchall():
                        entries.append(dict(row))

                    cache_data['cache_entries'] = entries

            except Exception as e:
                cache_data['error'] = str(e)

        return {'cache': cache_data, 'count': len(cache_data.get('cache_entries', []))}

    def _backup_logs(self) -> Dict[str, Any]:
        """Backup log data"""
        logs = {}

        # Backup structured logs
        log_db = self.data_dir / "logs" / "ai_schema_generation_structured.db"
        if log_db.exists():
            try:
                with sqlite3.connect(log_db) as conn:
                    conn.row_factory = sqlite3.Row

                    # Get recent logs (last 30 days)
                    since_date = (datetime.now() - timedelta(days=30)).isoformat()
                    cursor = conn.execute(
                        "SELECT * FROM log_entries WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 10000",
                        [since_date]
                    )

                    log_entries = []
                    for row in cursor.fetchall():
                        log_entries.append(dict(row))

                    logs['log_entries'] = log_entries

            except Exception as e:
                logs['error'] = str(e)

        return {'logs': logs, 'count': len(logs.get('log_entries', []))}

    def _backup_performance_metrics(self) -> Dict[str, Any]:
        """Backup performance metrics"""
        metrics = {}

        # Backup from performance database
        perf_db = self.data_dir / "performance_metrics.db"
        if perf_db.exists():
            try:
                with sqlite3.connect(perf_db) as conn:
                    conn.row_factory = sqlite3.Row

                    # Get recent metrics
                    since_date = (datetime.now() - timedelta(days=7)).isoformat()
                    cursor = conn.execute(
                        "SELECT * FROM performance_metrics WHERE timestamp > ?",
                        [since_date]
                    )

                    metric_entries = []
                    for row in cursor.fetchall():
                        metric_entries.append(dict(row))

                    metrics['performance_entries'] = metric_entries

            except Exception as e:
                metrics['error'] = str(e)

        return {'performance_metrics': metrics, 'count': len(metrics.get('performance_entries', []))}

    def _backup_validation_results(self) -> Dict[str, Any]:
        """Backup validation results"""
        validations = {}

        # Backup validation results
        validation_dir = self.data_dir / "validations"
        if validation_dir.exists():
            for validation_file in validation_dir.glob("*.json"):
                try:
                    with open(validation_file, 'r') as f:
                        validation_data = json.load(f)
                        validations[validation_file.stem] = validation_data
                except Exception as e:
                    validations[f"error_{validation_file.stem}"] = {'error': str(e)}

        return {'validation_results': validations, 'count': len(validations)}

    def _backup_ai_metadata(self) -> Dict[str, Any]:
        """Backup AI generation metadata"""
        ai_metadata = {}

        # Backup AI metadata
        ai_dir = self.data_dir / "ai_metadata"
        if ai_dir.exists():
            for metadata_file in ai_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        ai_metadata[metadata_file.stem] = metadata
                except Exception as e:
                    ai_metadata[f"error_{metadata_file.stem}"] = {'error': str(e)}

        return {'ai_metadata': ai_metadata, 'count': len(ai_metadata)}

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _register_backup(self, manifest: BackupManifest, backup_path: Path):
        """Register backup in the registry"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.execute("""
                INSERT INTO backups (
                    backup_id, backup_type, created_at, version, description,
                    file_count, total_size_bytes, checksum, components,
                    metadata, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                manifest.backup_id,
                manifest.backup_type.value,
                manifest.created_at,
                manifest.version,
                manifest.description,
                manifest.file_count,
                manifest.total_size_bytes,
                manifest.checksum,
                json.dumps(manifest.components),
                json.dumps(manifest.metadata),
                str(backup_path)
            ))

    def list_backups(self, backup_type: Optional[BackupType] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        """List available backups"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM backups WHERE is_valid = 1"
            params = []

            if backup_type:
                query += " AND backup_type = ?"
                params.append(backup_type.value)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)

            backups = []
            for row in cursor.fetchall():
                backup_dict = dict(row)
                # Parse JSON fields
                backup_dict['components'] = json.loads(backup_dict['components'])
                backup_dict['metadata'] = json.loads(backup_dict['metadata'])
                backups.append(backup_dict)

            return backups

    def restore_backup(self, backup_id: str, restore_mode: RestoreMode = RestoreMode.REPLACE,
                      target_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Restore from backup

        Args:
            backup_id: ID of backup to restore
            restore_mode: How to handle existing data
            target_components: Specific components to restore

        Returns:
            Restore result information
        """
        try:
            # Get backup information
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return {
                    'success': False,
                    'error': f'Backup {backup_id} not found',
                    'message': 'Backup not found in registry'
                }

            # Verify backup file exists and is valid
            backup_path = Path(backup_info['file_path'])
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': 'Backup file not found',
                    'message': f'Backup file not found: {backup_path}'
                }

            # Verify checksum
            current_checksum = self._calculate_file_checksum(backup_path)
            if current_checksum != backup_info['checksum']:
                return {
                    'success': False,
                    'error': 'Backup integrity check failed',
                    'message': 'Backup file appears to be corrupted'
                }

            # Perform restore
            restore_result = self._perform_restore(
                backup_path, backup_info, restore_mode, target_components
            )

            # Update restore statistics
            self._update_restore_stats(backup_id)

            return restore_result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to restore backup {backup_id}'
            }

    def _get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get backup information from registry"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM backups WHERE backup_id = ?", [backup_id]
            )
            row = cursor.fetchone()

            if row:
                backup_dict = dict(row)
                backup_dict['components'] = json.loads(backup_dict['components'])
                backup_dict['metadata'] = json.loads(backup_dict['metadata'])
                return backup_dict

            return None

    def _perform_restore(self, backup_path: Path, backup_info: Dict[str, Any],
                        restore_mode: RestoreMode,
                        target_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform the actual restore operation"""
        start_time = time.time()
        restored_components = []
        errors = []

        available_components = backup_info['components']
        if target_components:
            components_to_restore = [c for c in target_components if c in available_components]
        else:
            components_to_restore = available_components

        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            # Restore each component
            for component in components_to_restore:
                try:
                    component_path = f"components/{component}.json"
                    if component_path in zip_file.namelist():
                        component_data = json.loads(zip_file.read(component_path))
                        self._restore_component(component, component_data, restore_mode)
                        restored_components.append(component)
                    else:
                        errors.append(f"Component {component} not found in backup")

                except Exception as e:
                    errors.append(f"Failed to restore {component}: {str(e)}")

        return {
            'success': len(errors) == 0,
            'backup_id': backup_info['backup_id'],
            'restored_components': restored_components,
            'errors': errors,
            'duration_seconds': time.time() - start_time,
            'message': f'Restored {len(restored_components)} components'
        }

    def _restore_component(self, component: str, component_data: Dict[str, Any],
                          restore_mode: RestoreMode):
        """Restore a specific component"""
        if component == 'schemas':
            self._restore_schemas(component_data, restore_mode)
        elif component == 'extracted_data':
            self._restore_extracted_data(component_data, restore_mode)
        elif component == 'cache':
            self._restore_cache(component_data, restore_mode)
        elif component == 'logs':
            self._restore_logs(component_data, restore_mode)
        elif component == 'performance_metrics':
            self._restore_performance_metrics(component_data, restore_mode)
        elif component == 'validation_results':
            self._restore_validation_results(component_data, restore_mode)
        elif component == 'ai_metadata':
            self._restore_ai_metadata(component_data, restore_mode)

    def _restore_schemas(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore schema definitions"""
        schema_dir = self.data_dir / "schemas"
        schema_dir.mkdir(parents=True, exist_ok=True)

        schemas = data.get('schemas', {})
        for schema_id, schema_data in schemas.items():
            if schema_id.startswith('error_'):
                continue

            schema_file = schema_dir / f"{schema_id}.json"

            if mode == RestoreMode.SKIP_EXISTING and schema_file.exists():
                continue

            with open(schema_file, 'w') as f:
                json.dump(schema_data, f, indent=2)

    def _restore_extracted_data(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore extracted data"""
        data_dir = self.data_dir / "extractions"
        data_dir.mkdir(parents=True, exist_ok=True)

        extracted_data = data.get('extracted_data', {})
        for data_id, extraction_data in extracted_data.items():
            if data_id.startswith('error_'):
                continue

            data_file = data_dir / f"{data_id}.json"

            if mode == RestoreMode.SKIP_EXISTING and data_file.exists():
                continue

            with open(data_file, 'w') as f:
                json.dump(extraction_data, f, indent=2)

    def _restore_cache(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore cache data"""
        cache_data = data.get('cache', {})
        cache_entries = cache_data.get('cache_entries', [])

        if not cache_entries:
            return

        cache_dir = self.data_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_db = cache_dir / "cache.db"

        with sqlite3.connect(cache_db) as conn:
            # Create table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    tags TEXT,
                    size_bytes INTEGER,
                    content_hash TEXT
                )
            """)

            for entry in cache_entries:
                if mode == RestoreMode.SKIP_EXISTING:
                    existing = conn.execute("SELECT 1 FROM cache_entries WHERE key = ?", [entry['key']]).fetchone()
                    if existing:
                        continue

                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (key, file_path, created_at, expires_at, access_count,
                     last_accessed, tags, size_bytes, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry['key'], entry['file_path'], entry['created_at'],
                    entry['expires_at'], entry['access_count'], entry['last_accessed'],
                    entry['tags'], entry['size_bytes'], entry['content_hash']
                ))

    def _restore_logs(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore log data"""
        logs_data = data.get('logs', {})
        log_entries = logs_data.get('log_entries', [])

        if not log_entries:
            return

        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_db = log_dir / "ai_schema_generation_structured.db"

        with sqlite3.connect(log_db) as conn:
            # Create table if it doesn't exist
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

            for entry in log_entries:
                if mode == RestoreMode.SKIP_EXISTING:
                    # Check if similar entry exists (by timestamp and message)
                    existing = conn.execute(
                        "SELECT 1 FROM log_entries WHERE timestamp = ? AND message = ?",
                        [entry['timestamp'], entry['message']]
                    ).fetchone()
                    if existing:
                        continue

                conn.execute("""
                    INSERT INTO log_entries
                    (timestamp, level, logger_name, message, module, function,
                     line_number, thread_id, session_id, user_id, document_id,
                     schema_id, performance_metrics, ai_metadata, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry['timestamp'], entry['level'], entry['logger_name'],
                    entry['message'], entry['module'], entry['function'],
                    entry['line_number'], entry['thread_id'], entry['session_id'],
                    entry['user_id'], entry['document_id'], entry['schema_id'],
                    entry['performance_metrics'], entry['ai_metadata'], entry['extra_data']
                ))

    def _restore_performance_metrics(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore performance metrics"""
        # Similar to logs restoration but for performance data
        # Implementation would depend on the performance database structure
        pass

    def _restore_validation_results(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore validation results"""
        validation_dir = self.data_dir / "validations"
        validation_dir.mkdir(parents=True, exist_ok=True)

        validations = data.get('validation_results', {})
        for validation_id, validation_data in validations.items():
            if validation_id.startswith('error_'):
                continue

            validation_file = validation_dir / f"{validation_id}.json"

            if mode == RestoreMode.SKIP_EXISTING and validation_file.exists():
                continue

            with open(validation_file, 'w') as f:
                json.dump(validation_data, f, indent=2)

    def _restore_ai_metadata(self, data: Dict[str, Any], mode: RestoreMode):
        """Restore AI metadata"""
        ai_dir = self.data_dir / "ai_metadata"
        ai_dir.mkdir(parents=True, exist_ok=True)

        ai_metadata = data.get('ai_metadata', {})
        for metadata_id, metadata_data in ai_metadata.items():
            if metadata_id.startswith('error_'):
                continue

            metadata_file = ai_dir / f"{metadata_id}.json"

            if mode == RestoreMode.SKIP_EXISTING and metadata_file.exists():
                continue

            with open(metadata_file, 'w') as f:
                json.dump(metadata_data, f, indent=2)

    def _update_restore_stats(self, backup_id: str):
        """Update restore statistics for backup"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.execute("""
                UPDATE backups
                SET restored_count = restored_count + 1,
                    last_restored = ?
                WHERE backup_id = ?
            """, [datetime.now().isoformat(), backup_id])

    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """Delete a backup"""
        try:
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return {
                    'success': False,
                    'error': 'Backup not found',
                    'message': f'Backup {backup_id} not found'
                }

            # Delete backup file
            backup_path = Path(backup_info['file_path'])
            if backup_path.exists():
                backup_path.unlink()

            # Remove from registry
            with sqlite3.connect(self.registry_db) as conn:
                conn.execute("DELETE FROM backups WHERE backup_id = ?", [backup_id])

            return {
                'success': True,
                'backup_id': backup_id,
                'message': 'Backup deleted successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to delete backup {backup_id}'
            }

    def cleanup_old_backups(self, keep_count: int = 10, max_age_days: int = 90) -> Dict[str, Any]:
        """Clean up old backups"""
        try:
            deleted_count = 0
            total_size_freed = 0

            with sqlite3.connect(self.registry_db) as conn:
                # Get backups to delete (beyond keep_count or older than max_age_days)
                cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

                cursor = conn.execute("""
                    SELECT backup_id, file_path, total_size_bytes
                    FROM backups
                    WHERE created_at < ? OR backup_id NOT IN (
                        SELECT backup_id FROM backups
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                """, [cutoff_date, keep_count])

                backups_to_delete = cursor.fetchall()

                for backup_id, file_path, size_bytes in backups_to_delete:
                    # Delete file
                    backup_path = Path(file_path)
                    if backup_path.exists():
                        backup_path.unlink()
                        total_size_freed += size_bytes or 0

                    # Remove from registry
                    conn.execute("DELETE FROM backups WHERE backup_id = ?", [backup_id])
                    deleted_count += 1

            return {
                'success': True,
                'deleted_count': deleted_count,
                'size_freed_bytes': total_size_freed,
                'size_freed_mb': total_size_freed / (1024 * 1024),
                'message': f'Cleaned up {deleted_count} old backups'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to cleanup old backups'
            }

    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup system statistics"""
        with sqlite3.connect(self.registry_db) as conn:
            conn.row_factory = sqlite3.Row

            # Total backups
            total_backups = conn.execute("SELECT COUNT(*) FROM backups WHERE is_valid = 1").fetchone()[0]

            # Backups by type
            cursor = conn.execute("SELECT backup_type, COUNT(*) as count FROM backups WHERE is_valid = 1 GROUP BY backup_type")
            backups_by_type = {row['backup_type']: row['count'] for row in cursor.fetchall()}

            # Total storage used
            total_size = conn.execute("SELECT SUM(total_size_bytes) FROM backups WHERE is_valid = 1").fetchone()[0] or 0

            # Recent backup activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_backups = conn.execute(
                "SELECT COUNT(*) FROM backups WHERE is_valid = 1 AND created_at > ?", [week_ago]
            ).fetchone()[0]

            # Most recent backup
            cursor = conn.execute(
                "SELECT backup_id, created_at FROM backups WHERE is_valid = 1 ORDER BY created_at DESC LIMIT 1"
            )
            recent_backup = cursor.fetchone()

        return {
            'total_backups': total_backups,
            'backups_by_type': backups_by_type,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'recent_backup_activity': recent_backups,
            'most_recent_backup': {
                'backup_id': recent_backup['backup_id'],
                'created_at': recent_backup['created_at']
            } if recent_backup else None
        }


# Global backup manager instance
_backup_manager = None

def get_backup_manager() -> BackupManager:
    """Get singleton backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


def create_automated_backup(backup_type: BackupType = BackupType.FULL) -> Dict[str, Any]:
    """
    Convenience function to create automated backup

    Args:
        backup_type: Type of backup to create

    Returns:
        Backup result information
    """
    manager = get_backup_manager()
    return manager.create_backup(backup_type, f"Automated {backup_type.value} backup")