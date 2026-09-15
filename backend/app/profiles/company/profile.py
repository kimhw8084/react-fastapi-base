from __future__ import annotations

from app.platform.identity import IdentityProvider
from app.platform.profile import CompanyProfile
from app.platform.settings import Settings
from app.profiles.company.deployment import CompanyDeploymentAdapter
from app.profiles.company.identity import CompanyIdentity
from app.profiles.company.storage import CompanyStorageAdapter
from app.profiles.scanner import scanner_for


def create_profile(settings: Settings) -> CompanyProfile:
    identity: IdentityProvider = CompanyIdentity()
    return CompanyProfile(
        key='company',
        identity=identity,
        storage=CompanyStorageAdapter(),
        deployment=CompanyDeploymentAdapter(),
        malware_scanner=scanner_for(settings),
        require_startup_identity=True,
    )
