from __future__ import annotations

from app.platform.identity import IdentityProvider
from app.platform.profile import CompanyProfile
from app.platform.settings import Settings
from app.profiles.development.deployment import DevelopmentDeploymentAdapter
from app.profiles.development.storage import DevelopmentStorageAdapter
from app.profiles.scanner import scanner_for
from app.profiles.development.identity import DevelopmentIdentity


def create_profile(settings: Settings) -> CompanyProfile:
    identity: IdentityProvider = DevelopmentIdentity(settings.dev_user)
    return CompanyProfile(
        key='development',
        identity=identity,
        storage=DevelopmentStorageAdapter(),
        deployment=DevelopmentDeploymentAdapter(),
        malware_scanner=scanner_for(settings),
    )
