from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.platform.entity_registry import EntityRegistry
from app.platform.errors import AppError
from app.platform.models import SavedView
from app.platform.schemas import GlobalSearchResult
from app.platform.security import Actor

_TOKEN = re.compile(r'^(?P<key>[a-z][a-z0-9_-]{0,39}):(?P<value>[^\s]{1,120})$', re.IGNORECASE)


def _query_parts(query: str) -> tuple[str, str | None]:
    tokens = query.strip().split()
    terms: list[str] = []
    entity: str | None = None
    for token in tokens:
        match = _TOKEN.fullmatch(token)
        if match is None:
            terms.append(token)
        elif match.group('key').lower() in {'type', 'entity'}:
            entity = match.group('value').lower()
        # Other scoped tokens are deliberately excluded from the free-text
        # query. Feature adapters can add typed filters without changing this
        # platform search contract.
    return ' '.join(terms), entity


def global_search(
    session: Session,
    actor: Actor,
    registry: EntityRegistry,
    query: str,
    limit: int,
) -> list[GlobalSearchResult]:
    actor.require('read')
    if not query.strip() or len(query) > 200:
        raise AppError(422, 'invalid_search_query', 'Search must contain 1-200 characters.')
    if not 1 <= limit <= 100:
        raise AppError(422, 'invalid_search_limit', 'Search limit must be between 1 and 100.')
    text, entity_filter = _query_parts(query)
    if entity_filter is not None:
        registry.definition(entity_filter)
    results: list[GlobalSearchResult] = []
    seen: set[tuple[str, str]] = set()

    def add(row: GlobalSearchResult) -> None:
        key = (row.kind, row.id)
        if key not in seen and len(results) < limit:
            seen.add(key)
            results.append(row)

    for definition in registry.definitions():
        if entity_filter is not None and definition.key != entity_filter:
            continue
        for record in registry.search(session, definition.key, text or query, min(20, limit)):
            add(GlobalSearchResult(
                kind='record', id=record.id, label=record.label,
                description=definition.label, entity=record.entity,
                workspace=record.workspace,
            ))
            if len(results) >= limit:
                return results

    if entity_filter is None:
        needle = (text or query).casefold()
        views = session.scalars(select(SavedView).where(
            or_(SavedView.scope == 'team', SavedView.owner == actor.user_id),
            SavedView.name.ilike(f'%{needle}%'),
        ).order_by(SavedView.name).limit(limit)).all()
        for view in views:
            add(GlobalSearchResult(
                kind='saved_view', id=view.id, label=view.name,
                description=f'{view.scope} view · {view.workspace}',
                entity=None, workspace=view.workspace,
            ))
            if len(results) >= limit:
                break
    return results
