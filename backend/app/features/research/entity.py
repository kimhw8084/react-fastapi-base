from sqlalchemy import or_,select
from app.platform.entity_registry import EntityBinding
from app.platform.schemas import EntityDefinition,EntityReference
from .models import Research
from . import service
def _ref(row):return EntityReference(entity='research',id=row.id,label=str(getattr(row,'title')),workspace='research',archived=row.archived,revision=row.revision)
def resolve(session,record_id):
    row=session.get(Research,record_id);return _ref(row) if row else None
def search(session,query,limit):
    where=[]
    if query:
        escaped=query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_');where.append(or_(Research.title.ilike(f'%{escaped}%',escape='\\'),Research.question.ilike(f'%{escaped}%',escape='\\'),Research.hypothesis.ilike(f'%{escaped}%',escape='\\'),Research.methodology.ilike(f'%{escaped}%',escape='\\'),Research.analysis.ilike(f'%{escaped}%',escape='\\'),Research.findings.ilike(f'%{escaped}%',escape='\\'),Research.conclusion.ilike(f'%{escaped}%',escape='\\'),Research.recommendation.ilike(f'%{escaped}%',escape='\\')))
    return [_ref(row) for row in session.scalars(select(Research).where(*where).order_by(Research.archived,Research.title,Research.id).limit(limit)).all()]
def bulk_update(session,actor,targets,patch):
    rows=service.CRUD.bulk_update(session,actor,targets,patch)
    return [resolve(session,row.id) for row in rows]
def binding():return EntityBinding(EntityDefinition(key='research',label='Research',description='Canonical engineering research records for hypotheses, experiments, evidence, analysis and recommendations.',workspace='research',primary_field='title',authority='canonical',search_fields=['title', 'question', 'hypothesis', 'methodology', 'analysis', 'findings', 'conclusion', 'recommendation'],capabilities=['history','archive','saved_views','relationships']),resolve,search,bulk_update=bulk_update)
