from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from collections.abc import Callable, Mapping
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.schemas import EntityDefinition, EntityReference, RelationshipDefinition, EntityBulkUpdateTarget, WorkspaceDefinition

Resolver = Callable[[Session, str], EntityReference | None]
Searcher = Callable[[Session, str, int], list[EntityReference]]
BulkUpdater = Callable[[Session, object, list[EntityBulkUpdateTarget], dict], list[EntityReference]]

@dataclass(frozen=True)
class EntityBinding:
    definition: EntityDefinition
    resolve: Resolver
    search: Searcher
    bulk_update: BulkUpdater | None = None

class EntityRegistry:
    def __init__(self, bindings: Mapping[str, EntityBinding], relationship_definitions: list[RelationshipDefinition], workspace_definitions: Mapping[str, WorkspaceDefinition] | None = None):
        workspace_definitions = workspace_definitions or {}
        self._bindings = {}
        for key, binding in bindings.items():
            workspace = workspace_definitions.get(binding.definition.workspace)
            definition = binding.definition
            if workspace is not None:
                definition = definition.model_copy(update={
                    'schema_version': workspace.schema_version,
                    'fields': workspace.fields,
                    'columns': workspace.columns,
                    'visualizations': workspace.visualizations,
                })
            self._bindings[key] = EntityBinding(definition=definition,resolve=binding.resolve,search=binding.search,bulk_update=binding.bulk_update)
        for key, binding in self._bindings.items():
            if key != binding.definition.key:
                raise ValueError('Entity key/binding mismatch.')
        self._relationships = {item.key:item for item in relationship_definitions}
        if len(self._relationships) != len(relationship_definitions):
            raise ValueError('Relationship definition keys must be unique.')
        for relationship in relationship_definitions:
            if relationship.source_entity not in self._bindings or relationship.target_entity not in self._bindings:
                raise ValueError(f'Relationship {relationship.key} references an unregistered entity.')

    def definitions(self) -> list[EntityDefinition]:
        return [self._bindings[key].definition.model_copy(deep=True) for key in sorted(self._bindings)]

    def definition(self, key: str) -> EntityDefinition:
        binding=self._bindings.get(key)
        if not binding:
            raise AppError(404,'entity_missing','Entity is not registered.')
        return binding.definition.model_copy(deep=True)

    def resolve(self, session: Session, key: str, record_id: str) -> EntityReference:
        binding=self._bindings.get(key)
        if not binding:
            raise AppError(404,'entity_missing','Entity is not registered.')
        result=binding.resolve(session,record_id)
        if result is None:
            raise AppError(404,'record_missing','Related record was not found in this tenant.')
        return result

    def search(self, session: Session, key: str, query: str, limit: int) -> list[EntityReference]:
        if len(query)>200 or not 1<=limit<=100:
            raise AppError(422,'invalid_query','Invalid entity search query.')
        binding=self._bindings.get(key)
        if not binding:
            raise AppError(404,'entity_missing','Entity is not registered.')
        return binding.search(session,query,limit)

    def bulk_update(self, session: Session, actor, key: str, targets: list[EntityBulkUpdateTarget], patch: dict) -> list[EntityReference]:
        binding=self._bindings.get(key)
        if not binding:
            raise AppError(404,'entity_missing','Entity is not registered.')
        if binding.bulk_update is None:
            raise AppError(422,'bulk_update_unsupported','This entity does not support generic bulk updates.')
        return binding.bulk_update(session,actor,targets,patch)

    def relationship_definitions(self) -> list[RelationshipDefinition]:
        return [self._relationships[key].model_copy(deep=True) for key in sorted(self._relationships)]

    def relationship(self, key: str) -> RelationshipDefinition:
        value=self._relationships.get(key)
        if not value:
            raise AppError(404,'relationship_definition_missing','Relationship type is not registered.')
        return value.model_copy(deep=True)

def load_relationship_definitions(path: Path) -> list[RelationshipDefinition]:
    payload=json.loads(path.read_text()) if path.exists() else []
    if not isinstance(payload,list):
        raise ValueError('Relationship configuration must be a list.')
    return [RelationshipDefinition.model_validate(item) for item in payload]
