from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import ProcessRecipe
from .schemas import ProcessRecipeCreate,ProcessRecipeRead,ProcessRecipePage,ProcessRecipeBulkRequest
WORKSPACE='process_recipes'
SORTS={'name':ProcessRecipe.name,'version_name':ProcessRecipe.version_name,'process':ProcessRecipe.process,'status':ProcessRecipe.status,'approved_by':ProcessRecipe.approved_by,'approved_at':ProcessRecipe.approved_at,'updated_at':ProcessRecipe.updated_at,'created_at':ProcessRecipe.created_at,'created_by':ProcessRecipe.created_by,'revision':ProcessRecipe.revision}
CRUD=RevisionCrudService(model=ProcessRecipe,create_schema=ProcessRecipeCreate,read_schema=ProcessRecipeRead,workspace=WORKSPACE,not_found_label='Recipe')
QUERY=EntityQueryService(model=ProcessRecipe,read_schema=ProcessRecipeRead,sorts=SORTS,search_columns=(ProcessRecipe.name,ProcessRecipe.version_name,ProcessRecipe.process,ProcessRecipe.approved_by,ProcessRecipe.notes,),filters={'status':(ProcessRecipe.status,('draft', 'qualified', 'released', 'deprecated'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ProcessRecipePage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ProcessRecipeBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
