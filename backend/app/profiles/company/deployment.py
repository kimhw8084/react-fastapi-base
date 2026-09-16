from __future__ import annotations

from app.platform.settings import Settings


class CompanyDeploymentAdapter:
    """Delegate company qualification and deployment safety to Settings."""

    def assert_safe(self, settings: Settings, *, scanner_is_noop: bool | None = None) -> None:
        settings.assert_safe(scanner_is_noop=scanner_is_noop)

    def assert_maintenance_safe(self, settings: Settings) -> None:
        settings.assert_maintenance_safe()
