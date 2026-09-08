from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class NavigationItem(BaseModel):
    model_config = ConfigDict(extra='forbid',json_schema_serialization_defaults_required=True)
    workspace: str = Field(pattern=r'^[a-z][a-z0-9_]{0,39}$')
    label: str = Field(min_length=1, max_length=60)

class ApplicationConfig(BaseModel):
    model_config = ConfigDict(extra='forbid',json_schema_serialization_defaults_required=True)
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r'^[a-z][a-z0-9-]{0,39}$')
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=240)
    theme: Literal['operations', 'clarity', 'minimal'] = 'operations'
    density: Literal['comfortable', 'compact'] = 'comfortable'
    navigation: list[NavigationItem]
    support_url: str = ''
    @field_validator('support_url')
    @classmethod
    def safe_support_url(cls, value: str) -> str:
        if value and not value.startswith('https://'):
            raise ValueError('Support URL must use HTTPS.')
        return value
    @field_validator('navigation')
    @classmethod
    def unique_navigation(cls, values):
        keys = [item.workspace for item in values]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate workspace navigation.')
        return values

def load_config(path: Path) -> ApplicationConfig:
    return ApplicationConfig.model_validate_json(path.read_text())
