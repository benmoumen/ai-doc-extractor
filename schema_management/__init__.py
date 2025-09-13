"""
Schema Management UI Extension
Provides rich UI for creating, editing, and managing document schemas.
"""

from .schema_builder import render_schema_management_page

__version__ = "1.0.0"
__all__ = [
    "render_schema_management_page"
]