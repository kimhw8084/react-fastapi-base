from __future__ import annotations

from pathlib import Path

from app.platform.database import Database
from app.platform.profile import StorageAdapter
from app.platform.settings import Settings
from app.platform.storage import LocalFilesystemStorage, StorageBackupAdapter


class CompanyStorageAdapter(StorageAdapter):
    """The explicitly supported company persistence contract.

    The current company implementation is deliberately the same conservative
    POSIX-root/SQLite implementation as development, but it is selected only
    after the typed company storage facts have been validated.  Keeping this
    class independent prevents development semantics from becoming an
    accidental company guarantee through inheritance.
    """

    def _assert_storage_contract(self, settings: Settings) -> None:
        errors = settings.company_storage_errors()
        if errors:
            raise RuntimeError('Company storage refused: ' + ' '.join(errors))

    def build_database(self, settings: Settings) -> Database:
        self._assert_storage_contract(settings)
        return Database(settings)

    def build_object_storage(self, settings: Settings) -> StorageBackupAdapter:
        self._assert_storage_contract(settings)
        return LocalFilesystemStorage(settings.data_root / 'objects')

    def build_restore_object_storage(self, settings: Settings, target_root: Path) -> StorageBackupAdapter:
        self._assert_storage_contract(settings)
        return LocalFilesystemStorage(target_root / 'objects')
