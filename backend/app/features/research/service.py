from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import Research
from .schemas import ResearchCreate,ResearchRead,ResearchPage,ResearchBulkRequest
WORKSPACE='research'
SORTS={'title':Research.title,'status':Research.status,'phase':Research.phase,'updated_at':Research.updated_at,'created_at':Research.created_at,'created_by':Research.created_by,'revision':Research.revision}
CRUD=RevisionCrudService(model=Research,create_schema=ResearchCreate,read_schema=ResearchRead,workspace=WORKSPACE,not_found_label='Research Record')
QUERY=EntityQueryService(model=Research,read_schema=ResearchRead,sorts=SORTS,search_columns=(Research.title,Research.question,Research.hypothesis,Research.methodology,Research.analysis,Research.findings,Research.conclusion,Research.recommendation,),filters={'status':(Research.status,('question', 'researching', 'experimenting', 'analyzing', 'review', 'complete')),'phase':(Research.phase,('discovery', 'hypothesis', 'experiment', 'analysis', 'conclusion'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ResearchPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ResearchBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
