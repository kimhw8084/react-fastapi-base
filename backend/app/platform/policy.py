from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class Policy(BaseModel):
    """Server-owned authorization policy. Never load this from browser configuration."""
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    roles: dict[str, list[str]]
    def permissions(self, role: str) -> frozenset[str]:
        return frozenset(self.roles.get(role, []))

def load_policy(path: Path) -> Policy:
    policy = Policy.model_validate_json(path.read_text())
    # This release's SQL schema uses a finite role vocabulary.
    if set(policy.roles) != {'viewer', 'editor', 'admin'}:
        raise ValueError('Changing role identifiers requires a schema migration.')
    if 'read' not in policy.permissions('admin') or 'admin' not in policy.permissions('admin'):
        raise ValueError('Administrator policy must retain read and administration permissions.')
    return policy
