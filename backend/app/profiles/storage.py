"""Profile-owned construction of the existing local persistence adapters."""
from __future__ import annotations

from dataclasses import dataclass

from app.platform.database import Database
from app.platform.profile import StorageAdapter
from app.platform.settings import Settings
from app.platform.storage import LocalFilesystemStorage, StorageBackupAdapter


@dataclass(frozen=True)
class LocalStorageAdapter(StorageAdapter):
    """Use the existing safe local adapters without provisioning on startup."""

    def build_database(self, settings: Settings) -> Database:
        return Database(settings)

    def build_object_storage(self, settings: Settings) -> StorageBackupAdapter:
        return LocalFilesystemStorage(settings.data_root / 'objects')
