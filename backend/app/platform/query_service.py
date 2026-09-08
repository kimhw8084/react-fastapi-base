from __future__ import annotations
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.security import Actor

class EntityQueryService:
    def __init__(self, *, model, read_schema, sorts: dict, search_columns: tuple, filters: dict[str, tuple]):
        self.model=model;self.read_schema=read_schema;self.sorts=sorts;self.search_columns=search_columns;self.filters=filters
    def list(self, session:Session, actor:Actor, *, page_schema, search:str='', filter_values:dict[str,str]|None=None, archived:bool=False, sort:str='updated_at', direction:str='desc', limit:int=50, offset:int=0):
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
            if len(rule)==2:column,allowed=rule;coerce=lambda item:item
            elif len(rule)==3:column,allowed,coerce=rule
            else:raise RuntimeError('Invalid filter rule configuration.')
            if allowed and value not in allowed:raise AppError(422,'invalid_filter','Invalid filter value.')
            try:normalized=coerce(value)
            except (TypeError,ValueError):raise AppError(422,'invalid_filter','Invalid filter value.')
            where.append(column==normalized)
        total=session.scalar(select(func.count()).select_from(self.model).where(*where)) or 0
        column=self.sorts[sort];order=column.asc() if direction=='asc' else column.desc()
        rows=session.scalars(select(self.model).where(*where).order_by(order,self.model.id).limit(limit).offset(offset)).all()
        return page_schema(items=[self.read_schema.model_validate(row) for row in rows],total=total,limit=limit,offset=offset)
