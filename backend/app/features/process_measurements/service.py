from math import isfinite
from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import ProcessMeasurement
from .schemas import ProcessMeasurementCreate,ProcessMeasurementRead,ProcessMeasurementPage,ProcessMeasurementBulkRequest
WORKSPACE='process_measurements'
SORTS={'sample_label':ProcessMeasurement.sample_label,'process':ProcessMeasurement.process,'metric':ProcessMeasurement.metric,'value':ProcessMeasurement.value,'unit':ProcessMeasurement.unit,'sampled_at':ProcessMeasurement.sampled_at,'subgroup':ProcessMeasurement.subgroup,'lot':ProcessMeasurement.lot,'category':ProcessMeasurement.category,'updated_at':ProcessMeasurement.updated_at,'created_at':ProcessMeasurement.created_at,'created_by':ProcessMeasurement.created_by,'revision':ProcessMeasurement.revision}

def normalize_measurement(values):
    values=dict(values)
    for key in ('value','target','lower_spec','upper_spec'):
        value=values.get(key)
        if value is not None and not isfinite(float(value)):
            raise AppError(422,'invalid_measurement',f'{key.replace("_"," ").title()} must be a finite number.')
    lower=values.get('lower_spec');upper=values.get('upper_spec');target=values.get('target')
    if lower is not None and upper is not None and float(lower)>=float(upper):
        raise AppError(422,'invalid_specification','Lower specification limit must be below upper specification limit.')
    if target is not None and lower is not None and float(target)<float(lower):
        raise AppError(422,'invalid_specification','Target must not be below the lower specification limit.')
    if target is not None and upper is not None and float(target)>float(upper):
        raise AppError(422,'invalid_specification','Target must not exceed the upper specification limit.')
    return values

CRUD=RevisionCrudService(model=ProcessMeasurement,create_schema=ProcessMeasurementCreate,read_schema=ProcessMeasurementRead,workspace=WORKSPACE,not_found_label='Measurement',normalize_values=normalize_measurement)
QUERY=EntityQueryService(model=ProcessMeasurement,read_schema=ProcessMeasurementRead,sorts=SORTS,search_columns=(ProcessMeasurement.sample_label,ProcessMeasurement.process,ProcessMeasurement.metric,ProcessMeasurement.unit,ProcessMeasurement.subgroup,ProcessMeasurement.lot,),filters={'category':(ProcessMeasurement.category,('measurement', 'defect', 'alarm', 'quality'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=ProcessMeasurementPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:ProcessMeasurementBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
