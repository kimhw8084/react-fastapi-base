from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.platform.errors import AppError
from app.platform.models import WorkspaceTeam, WorkspaceTeamMember, utcnow
from app.platform.schemas import TeamCreate, TeamRead, TeamMemberRead, TeamMemberWrite
from app.platform.security import Actor

def _read(session: Session, row: WorkspaceTeam) -> TeamRead:
    count=session.scalar(select(func.count()).select_from(WorkspaceTeamMember).where(WorkspaceTeamMember.team_id==row.id)) or 0
    return TeamRead.model_validate({'id':row.id,'name':row.name,'slug':row.slug,'owner':row.owner,'is_default':row.is_default,'revision':row.revision,'member_count':count,'updated_at':row.updated_at})

def default_team(session: Session, actor: Actor) -> WorkspaceTeam:
    row=session.scalar(select(WorkspaceTeam).where(WorkspaceTeam.is_default.is_(True)))
    if row is None:
        row=WorkspaceTeam(id=str(uuid4()),name='Workspace team',slug='workspace-team',owner=actor.user_id,is_default=True,revision=1,created_at=utcnow(),updated_at=utcnow())
        session.add(row);session.flush()
    return row

def list_teams(session: Session, actor: Actor) -> list[TeamRead]:
    actor.require('read')
    rows=session.scalars(select(WorkspaceTeam).order_by(WorkspaceTeam.is_default.desc(),WorkspaceTeam.name)).all()
    visible=[]
    for row in rows:
        if row.is_default or session.get(WorkspaceTeamMember,(row.id,actor.user_id)) is not None or row.owner==actor.user_id:
            visible.append(_read(session,row))
    return visible

def create_team(session: Session, actor: Actor, data: TeamCreate) -> TeamRead:
    actor.require('admin')
    if session.scalar(select(WorkspaceTeam).where(WorkspaceTeam.slug==data.slug)):
        raise AppError(409,'team_exists','A team with this slug already exists.')
    row=WorkspaceTeam(id=str(uuid4()),name=data.name.strip(),slug=data.slug,owner=actor.user_id,is_default=False,revision=1,created_at=utcnow(),updated_at=utcnow())
    session.add(row);session.flush();session.add(WorkspaceTeamMember(team_id=row.id,user_id=actor.user_id,role='manager'));session.flush()
    return _read(session,row)

def add_member(session: Session, actor: Actor, team_id: str, data: TeamMemberWrite) -> TeamMemberRead:
    actor.require('admin')
    team=session.get(WorkspaceTeam,team_id)
    if team is None:raise AppError(404,'team_missing','Team is not available.')
    row=session.get(WorkspaceTeamMember,(team_id,data.user_id))
    if row is None:row=WorkspaceTeamMember(team_id=team_id,user_id=data.user_id,role=data.role);session.add(row)
    else:row.role=data.role
    team.revision+=1;team.updated_at=utcnow();session.flush();return TeamMemberRead.model_validate(row)

def can_access(session: Session, actor: Actor, team_id: str | None) -> bool:
    if not team_id:return True
    if actor.role == 'admin':return True
    team=session.get(WorkspaceTeam,team_id)
    return bool(team and (team.is_default or team.owner==actor.user_id or session.get(WorkspaceTeamMember,(team_id,actor.user_id)) is not None))
