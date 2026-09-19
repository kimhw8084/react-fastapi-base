from __future__ import annotations

from app.platform.settings import Settings
from app.platform.deployment_contract import company_deployment_contract_errors


class CompanyDeploymentAdapter:
    """Delegate company qualification and deployment safety to Settings."""

    def assert_safe(self, settings: Settings, *, scanner_is_noop: bool | None = None) -> None:
        errors = company_deployment_contract_errors(settings)
        if errors:
            raise RuntimeError('Company deployment contract refused: ' + ' '.join(errors))
        settings.assert_safe(scanner_is_noop=scanner_is_noop)

    def assert_maintenance_safe(self, settings: Settings) -> None:
        errors = company_deployment_contract_errors(settings)
        if errors:
            raise RuntimeError('Company deployment contract refused: ' + ' '.join(errors))
        settings.assert_maintenance_safe()
