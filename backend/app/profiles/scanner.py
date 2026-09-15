"""Profile-local selection of the existing attachment scanner behavior."""
from __future__ import annotations

from app.platform.attachments import DeterministicMalwareScanner, MalwareScanner, NoopMalwareScanner
from app.platform.settings import Settings


def scanner_for(settings: Settings) -> MalwareScanner | None:
    if settings.attachment_upload_mode == 'disabled':
        return None
    if settings.environment in ('development', 'test'):
        return DeterministicMalwareScanner()
    return NoopMalwareScanner()
