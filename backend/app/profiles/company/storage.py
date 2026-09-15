from __future__ import annotations

from app.profiles.storage import LocalStorageAdapter


class CompanyStorageAdapter(LocalStorageAdapter):
    """Retain the existing local adapter until company storage is qualified."""
