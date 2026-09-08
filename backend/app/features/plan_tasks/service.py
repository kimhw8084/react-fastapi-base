from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import PlanTask
from .schemas import PlanTaskCreate,PlanTaskRead,PlanTaskPage,PlanTaskBulkRequest
WORKSPACE='plan_tasks'
SORTS={'title':PlanTask.title,'status':PlanTask.status,'start_date':PlanTask.start_date,'end_date':PlanTask.end_date,'baseline_start':PlanTask.baseline_start,'baseline_end':PlanTask.baseline_end,'progress':PlanTask.progress,'milestone':PlanTask.milestone,'owner':PlanTask.owner,'resource_group':PlanTask.resource_group,'effort_hours':PlanTask.effort_hours,'capacity_hours':PlanTask.capacity_hours,'duration_days':PlanTask.duration_days,'updated_at':PlanTask.updated_at,'created_at':PlanTask.created_at,'created_by':PlanTask.created_by,'revision':PlanTask.revision}
def normalize_plan(values):
    values=dict(values)
    start=values['start_date'];end=values['end_date']
    if end<start:raise AppError(422,'invalid_schedule','End date cannot precede start date.')
    baseline_start=values.get('baseline_start');baseline_end=values.get('baseline_end')
    if (baseline_start is None)!=(baseline_end is None):raise AppError(422,'invalid_baseline','Baseline start and end must be supplied together.')
    if baseline_start is not None and baseline_end<baseline_start:raise AppError(422,'invalid_baseline','Baseline end cannot precede baseline start.')
    if values.get('milestone') and end!=start:raise AppError(422,'invalid_milestone','Milestones must start and end on the same date.')
    values['duration_days']=(end-start).days+1
    if values.get('effort_hours') is None: values['effort_hours']=values['duration_days']*8.0
    if values.get('capacity_hours') is None: values['capacity_hours']=8.0
    return values
CRUD=RevisionCrudService(model=PlanTask,create_schema=PlanTaskCreate,read_schema=PlanTaskRead,workspace=WORKSPACE,not_found_label='Plan Task',normalize_values=normalize_plan)
QUERY=EntityQueryService(model=PlanTask,read_schema=PlanTaskRead,sorts=SORTS,search_columns=(PlanTask.title,PlanTask.owner,PlanTask.notes,),filters={'status':(PlanTask.status,('planned', 'ready', 'in_progress', 'blocked', 'done', 'cancelled')),'milestone':(PlanTask.milestone,('true','false'),lambda value:value=='true')})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=PlanTaskPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:PlanTaskBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
