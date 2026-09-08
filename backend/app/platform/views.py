from uuid import uuid4
from sqlalchemy import or_, select, update, delete
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import SavedView, utcnow
from app.platform.schemas import ViewCreate, ViewUpdate, ViewRead, ViewDefinition, WorkspaceDefinition
from app.platform.security import Actor
from app.platform import teams

def sanitize_view(definition: WorkspaceDefinition, value: ViewDefinition) -> dict:
    columns = set(definition.columns)
    fields = {field.key:field for field in definition.fields}
    data = value.model_dump()
    for key, selected in data['filters'].items():
        if key not in definition.filter_keys or key not in fields or selected not in fields[key].choices:
            raise AppError(422,'invalid_saved_filter','Saved filter is not supported.')
    if data['group_by'] and data['group_by'] not in definition.filter_keys:
        raise AppError(422,'invalid_saved_group','Saved grouping is not supported.')
    if data['sort'] not in definition.sort_keys:
        raise AppError(422,'invalid_saved_sort','Saved ordering is not supported.')
    for sort in data['sorts']:
        if sort['key'] not in definition.sort_keys:
            raise AppError(422,'invalid_saved_sort','Saved multi-ordering is not supported.')
    if data['visualization'] not in definition.visualizations:
        raise AppError(422,'invalid_saved_visualization','Saved visualization is not supported.')
    seen = set()
    data['columns'] = [c for c in data['columns'] if c['colId'] in columns and not (c['colId'] in seen or seen.add(c['colId']))]
    data['schema_version']=2
    return data

def migrate_definition(value: dict) -> dict:
    """Upgrade persisted view state without retaining removed fields."""
    data=dict(value or {})
    if not isinstance(data.get('advanced_filters'),list): data['advanced_filters']=[]
    if not isinstance(data.get('sorts'),list):
        data['sorts']=[{'key':data.get('sort','updated_at'),'direction':data.get('direction','desc')}]
    data['schema_version']=2
    return data

def list_views(session: Session, actor: Actor, workspace: str) -> list[ViewRead]:
    rows=session.scalars(select(SavedView).where(SavedView.workspace==workspace,or_(SavedView.scope=='team',SavedView.owner==actor.user_id)).order_by(SavedView.name).limit(200)).all()
    rows=[row for row in rows if row.scope=='personal' or teams.can_access(session,actor,row.team_id)]
    return [ViewRead.model_validate(row).model_copy(update={'definition':ViewDefinition.model_validate(migrate_definition(row.definition))}) for row in rows]

def get_view(session: Session, actor: Actor, workspace: str, view_id: str) -> SavedView:
    row=session.get(SavedView,view_id)
    if row is None or row.workspace!=workspace or (row.scope=='personal' and row.owner!=actor.user_id) or (row.scope=='team' and not teams.can_access(session,actor,row.team_id)):
        raise AppError(404,'view_missing','Saved view is not available.')
    return row

def create_view(session: Session, actor: Actor, workspace: str, data: ViewCreate, definition: WorkspaceDefinition) -> ViewRead:
    actor.require('views.team' if data.scope=='team' else 'views.personal')
    team_id=None
    if data.scope=='team':
        team=teams.default_team(session,actor) if data.team_id is None else session.get(teams.WorkspaceTeam,data.team_id)
        if team is None or not teams.can_access(session,actor,team.id):raise AppError(403,'team_forbidden','You are not a member of this team.')
        team_id=team.id
    row=SavedView(id=str(uuid4()),workspace=workspace,owner=actor.user_id,name=data.name,scope=data.scope,team_id=team_id,
                  definition=sanitize_view(definition,data.definition),revision=1,schema_version=2)
    session.add(row);session.flush()
    return ViewRead.model_validate(row)

def update_view(session: Session, actor: Actor, workspace: str, view_id: str, data: ViewUpdate, definition: WorkspaceDefinition) -> ViewRead:
    row=get_view(session,actor,workspace,view_id)
    if row.owner!=actor.user_id and not (row.scope=='team' and actor.role=='admin'):
        raise AppError(403,'view_forbidden','Only the owner or a team administrator may change this view.')
    actor.require('views.team' if data.scope=='team' else 'views.personal')
    if data.revision!=row.revision:
        current=ViewRead.model_validate(row).model_copy(update={'definition':ViewDefinition.model_validate(migrate_definition(row.definition))})
        raise AppError(409,'view_conflict','The saved view changed on the server.',{'current':current.model_dump(mode='json')})
    team_id=None
    if data.scope=='team':
        team=teams.default_team(session,actor) if data.team_id is None else session.get(teams.WorkspaceTeam,data.team_id)
        if team is None or not teams.can_access(session,actor,team.id):raise AppError(403,'team_forbidden','You are not a member of this team.')
        team_id=team.id
    row.name=data.name;row.scope=data.scope;row.team_id=team_id;row.definition=sanitize_view(definition,data.definition);row.schema_version=2
    row.revision+=1;row.updated_at=utcnow()
    session.flush()
    return ViewRead.model_validate(row)

def delete_view(session: Session, actor: Actor, workspace: str, view_id: str, revision: int):
    row=get_view(session,actor,workspace,view_id)
    if row.owner!=actor.user_id and not (row.scope=='team' and actor.role=='admin'):
        raise AppError(403,'view_forbidden','You cannot remove this view.')
    if row.revision!=revision:
        raise AppError(409,'view_conflict','The saved view changed on the server.')
    session.delete(row)
