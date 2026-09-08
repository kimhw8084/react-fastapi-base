from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from app.platform.security import Actor
from .models import Project
from .schemas import ProjectCreate,ProjectRead,ProjectPage,ProjectBulkRequest

WORKSPACE='projects'
SORTS={'title':Project.title,'status':Project.status,'owner':Project.owner,'updated_at':Project.updated_at,'created_at':Project.created_at,'created_by':Project.created_by,'revision':Project.revision}
CRUD=RevisionCrudService(model=Project,create_schema=ProjectCreate,read_schema=ProjectRead,workspace=WORKSPACE,not_found_label='Project')

QUERY=EntityQueryService(model=Project,read_schema=ProjectRead,sorts=SORTS,search_columns=(Project.title,Project.summary,Project.owner),filters={'status':(Project.status,('planned','active','blocked','complete'))})

def list_projects(session:Session,actor:Actor,*,search='',status='',archived=False,sort='updated_at',direction='desc',limit=50,offset=0):
    return QUERY.list(session,actor,page_schema=ProjectPage,search=search,filter_values={'status':status},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)

def bulk(session,actor,data:ProjectBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
