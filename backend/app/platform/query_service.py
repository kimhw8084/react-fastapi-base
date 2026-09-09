from __future__ import annotations
import json
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.security import Actor

class EntityQueryService:
    def __init__(self, *, model, read_schema, sorts: dict, search_columns: tuple, filters: dict[str, tuple]):
        self.model=model;self.read_schema=read_schema;self.sorts=sorts;self.search_columns=search_columns;self.filters=filters
    def list(self, session:Session, actor:Actor, *, page_schema, search:str='', filter_values:dict[str,str]|None=None, archived:bool=False, sort:str='updated_at', direction:str='desc', limit:int=50, offset:int=0, sorts:list[dict[str,Any]]|None=None, advanced_filters:list[dict[str,Any]]|None=None):
        actor.require('read');filter_values=filter_values or {}
        if sort not in self.sorts or direction not in ('asc','desc') or not 1<=limit<=1000 or offset<0 or len(search)>200:
            raise AppError(422,'invalid_query','Invalid list query.')
        unknown=set(filter_values)-set(self.filters)
        if unknown:raise AppError(422,'invalid_filter','Unknown filter key.')
        where=[self.model.archived==archived]
        if search:
            escaped=search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            where.append(or_(*(column.ilike(f'%{escaped}%',escape='\\') for column in self.search_columns)))
        for key,value in filter_values.items():
            if not value:continue
            rule=self.filters[key]
            if len(rule)==2:column,allowed=rule;coerce=lambda item:item;kind=None
            elif len(rule)==3:column,allowed,coerce=rule;kind=None
            elif len(rule)==4:column,allowed,coerce,kind=rule
            else:raise RuntimeError('Invalid filter rule configuration.')
            if allowed and value not in allowed:raise AppError(422,'invalid_filter','Invalid filter value.')
            try:normalized=coerce(value)
            except (TypeError,ValueError):raise AppError(422,'invalid_filter','Invalid filter value.')
            where.append(column==normalized)
        for item in advanced_filters or []:
            if not isinstance(item, dict) or not isinstance(item.get('key'), str) or not isinstance(item.get('value'), str):
                raise AppError(422,'invalid_advanced_filter','Advanced filter is invalid.')
            key, operator, value = item['key'], item.get('operator','eq'), item['value']
            if key not in self.filters or operator not in {'eq','neq','contains','starts_with','gt','gte','lt','lte'}:
                raise AppError(422,'invalid_advanced_filter','Advanced filter is not supported.')
            rule=self.filters[key]
            column,allowed = rule[0],rule[1]
            coerce = rule[2] if len(rule) in (3,4) else (lambda item:item)
            kind = rule[3] if len(rule)==4 else None
            if operator in {'eq','neq'}:
                if allowed and value not in allowed: raise AppError(422,'invalid_advanced_filter','Advanced filter value is invalid.')
                try: normalized=coerce(value)
                except (TypeError,ValueError): raise AppError(422,'invalid_advanced_filter','Advanced filter value is invalid.')
                where.append(column==normalized if operator=='eq' else column!=normalized)
            elif operator in {'contains','starts_with'}:
                if kind not in (None,'text'):
                    raise AppError(422,'invalid_advanced_filter','Text operators are not supported for this field.')
                if not isinstance(value,str) or len(value)>200: raise AppError(422,'invalid_advanced_filter','Advanced filter value is invalid.')
                escaped=value.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
                where.append(column.ilike(f"%{escaped}%" if operator=='contains' else f"{escaped}%",escape='\\'))
            else:
                try: normalized=coerce(value)
                except (TypeError,ValueError): raise AppError(422,'invalid_advanced_filter','Advanced filter value is invalid.')
                expression={'gt':column>normalized,'gte':column>=normalized,'lt':column<normalized,'lte':column<=normalized}[operator]
                where.append(expression)
        total=session.scalar(select(func.count()).select_from(self.model).where(*where)) or 0
        orderings=[]
        requested=sorts or [{'key':sort,'direction':direction}]
        if len(requested)>8: raise AppError(422,'invalid_query','At most eight sort keys are supported.')
        for item in requested:
            if not isinstance(item,dict) or item.get('key') not in self.sorts or item.get('direction') not in ('asc','desc'):
                raise AppError(422,'invalid_query','Invalid multi-sort state.')
            column=self.sorts[item['key']];orderings.append(column.asc() if item['direction']=='asc' else column.desc())
        rows=session.scalars(select(self.model).where(*where).order_by(*orderings,self.model.id).limit(limit).offset(offset)).all()
        return page_schema(items=[self.read_schema.model_validate(row) for row in rows],total=total,limit=limit,offset=offset)


def decode_query_list(raw: str, *, name: str, limit: int = 20) -> list[dict[str,Any]]:
    """Decode bounded JSON query state without accepting arbitrary structures."""
    if not raw:
        return []
    try:
        value=json.loads(raw)
    except (TypeError,ValueError):
        raise AppError(422,'invalid_query',f'{name} must be valid JSON.') from None
    if not isinstance(value,list) or len(value)>limit or any(not isinstance(item,dict) for item in value):
        raise AppError(422,'invalid_query',f'{name} must be a bounded list of objects.')
    return value
