"""Company-neutral contracts for server profile composition.

The application composition root selects one trusted profile implementation.
This module contains only ports and the server-side runtime object; it never
imports a concrete company or development provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from fastapi import Request

from app.platform.attachments import MalwareScanner, NoopMalwareScanner
from app.platform.database import Database
from app.platform.identity import IdentityProvider
from app.platform.settings import Settings
from app.platform.storage import ObjectStorageAdapter, StorageBackupAdapter


class StorageAdapter(Protocol):
    """Construct persistence services without provisioning or qualifying them."""

    def build_database(self, settings: Settings) -> Database: ...

    def build_object_storage(self, settings: Settings) -> StorageBackupAdapter: ...


StoragePort = StorageAdapter


class DeploymentAdapter(Protocol):
    """Own profile runtime validation while delegating existing safety rules."""

    def assert_safe(self, settings: Settings, *, scanner_is_noop: bool | None = None) -> None: ...

    def assert_maintenance_safe(self, settings: Settings) -> None: ...


DeploymentPort = DeploymentAdapter


@dataclass(frozen=True)
class CompanyProfile:
    """The canonical server-side profile composition contract.

    ``key`` is an internal trusted configuration identity. The object is never
    serialized into API or frontend runtime contracts.
    """

    key: Literal['development', 'company']
    identity: IdentityProvider
    storage: StorageAdapter
    deployment: DeploymentAdapter
    malware_scanner: MalwareScanner | None = None
    require_startup_identity: bool = False

    def build_runtime(self, settings: Settings) -> ProfileRuntime:
        return ProfileRuntime(
            profile=self,
            settings=settings,
            database=self.storage.build_database(settings),
            storage=self.storage,
            object_storage=self.storage.build_object_storage(settings),
            identity=self.identity,
            deployment=self.deployment,
            malware_scanner=self.malware_scanner,
        )


@dataclass(frozen=True)
class ProfileRuntime:
    """One fully wired server runtime produced by a trusted profile."""

    profile: CompanyProfile
    settings: Settings
    database: Database
    storage: StorageAdapter
    object_storage: ObjectStorageAdapter
    identity: IdentityProvider
    deployment: DeploymentAdapter
    malware_scanner: MalwareScanner | None

    @property
    def key(self) -> str:
        return self.profile.key

    def resolve_identity(self, request: Request) -> str:
        return self.identity.resolve(request)

    def assert_safe(self) -> None:
        scanner_is_noop = None if self.malware_scanner is None else isinstance(self.malware_scanner, NoopMalwareScanner)
        self.deployment.assert_safe(
            self.settings,
            scanner_is_noop=scanner_is_noop,
        )

    def assert_maintenance_safe(self) -> None:
        self.deployment.assert_maintenance_safe(self.settings)
