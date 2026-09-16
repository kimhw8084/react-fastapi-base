"""Trusted profile selection at the application composition boundary."""
from __future__ import annotations

from collections.abc import Callable

from app.platform.profile import CompanyProfile
from app.platform.settings import Settings
from app.profiles.company.profile import create_profile as create_company_profile
from app.profiles.development.profile import create_profile as create_development_profile


_PROFILE_FACTORIES: dict[str, Callable[[Settings], CompanyProfile]] = {
    'company': create_company_profile,
    'development': create_development_profile,
}


def load_profile(settings: Settings) -> CompanyProfile:
    """Load one statically trusted profile selected by server configuration."""
    try:
        factory = _PROFILE_FACTORIES[settings.profile]
    except KeyError as error:
        raise ValueError(f'Unsupported server profile: {settings.profile!r}') from error
    return factory(settings)
