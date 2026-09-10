from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select
from app.platform.security import Actor, actor_for, csrf_token
from app.platform.models import Membership, Tenant, AuditEvent, Attachment
from app.platform.schemas import Bootstrap, TenantInfo, ViewCreate, ViewUpdate, ViewRead, WorkspaceDefinition, AuditRead, EntityDefinition, EntityReference, EntityBulkUpdateRequest, EntityBulkUpdateResult, RelationshipDefinition, RelationshipCreate, RelationshipRead, RelationshipUpdate, RevisionInput, GlobalSearchResult, AttachmentRead
from app.platform.errors import AppError
from app.platform.idempotency import execute_once
from app.platform.transactions import write_transaction
from app.platform.version import VERSION
from app.platform import views, relationships, search
from app.platform.attachments import AttachmentUpload, attach, read_content

router=APIRouter(tags=['Platform'])
A=Annotated[Actor,Depends(actor_for)]

@router.get('/bootstrap',response_model=Bootstrap,operation_id='bootstrap')
def bootstrap(request: Request):
    user=request.app.state.identity.current_user()
    with request.app.state.database.session() as db:
        rows=db.execute(select(Tenant,Membership).join(Membership,Membership.tenant_id==Tenant.id).where(Membership.user_id==user,Tenant.active.is_(True)).order_by(Tenant.name)).all()
        return Bootstrap(user_id=user,profile=request.app.state.settings.profile,
            csrf_token=csrf_token(request.app.state.csrf_secret,user),
            tenants=[TenantInfo(id=tenant.id,name=tenant.name,role=membership.role,permissions=sorted(request.app.state.policy.permissions(membership.role))) for tenant,membership in rows],
            application=request.app.state.application.model_dump(),build_version=VERSION)

@router.get('/workspaces',response_model=list[WorkspaceDefinition],operation_id='listWorkspaces')
def workspaces(request: Request,actor: A):
    return [request.app.state.workspaces.get(item.workspace) for item in request.app.state.application.navigation]

@router.get('/workspaces/{workspace}/views',response_model=list[ViewRead],operation_id='listViews')
def list_views(request: Request,actor: A,workspace: str):
    request.app.state.workspaces.get(workspace)
    with request.app.state.database.session(actor.tenant_id) as db:
        return views.list_views(db,actor,workspace)

@router.post('/workspaces/{workspace}/views',response_model=ViewRead,status_code=201,operation_id='createView')
def create_view(request: Request,actor: A,workspace: str,data: ViewCreate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return views.create_view(db,actor,workspace,data,request.app.state.workspaces.get(workspace))

@router.put('/workspaces/{workspace}/views/{view_id}',response_model=ViewRead,operation_id='updateView')
def update_view(request: Request,actor: A,workspace: str,view_id: str,data: ViewUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return views.update_view(db,actor,workspace,view_id,data,request.app.state.workspaces.get(workspace))

@router.delete('/workspaces/{workspace}/views/{view_id}',status_code=204,operation_id='deleteView')
def delete_view(request: Request,actor: A,workspace: str,view_id: str,revision: int=Query(...,ge=1)):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        views.delete_view(db,actor,workspace,view_id,revision)
    return Response(status_code=204)

@router.get('/audit',response_model=list[AuditRead],operation_id='listAudit')
def audit(request: Request,actor: A,limit: int=Query(50,ge=1,le=200),workspace: str|None=Query(default=None,max_length=80),entity_id: str|None=Query(default=None,max_length=64)):
    if not workspace and not entity_id: actor.require('admin')
    else: actor.require('read')
    with request.app.state.database.session(actor.tenant_id) as db:
        query=select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        if workspace: query=query.where(AuditEvent.workspace==workspace)
        if entity_id: query=query.where(AuditEvent.entity_id==entity_id)
        return [AuditRead.model_validate(row) for row in db.scalars(query).all()]


@router.get('/identity-proof',operation_id='identityProof')
def identity_proof(request: Request,actor: A):
    """Safe observations for paired-user qualification; not an automatic certificate."""
    return {'user_id':actor.user_id,'instance_id':request.app.state.instance_id,
            'deployment_id':request.app.state.settings.deployment_id,
            'profile':request.app.state.settings.profile,
            'identity_source':'process_environment' if request.app.state.settings.profile=='company' else 'explicit_development_fixture'}


@router.get('/workspaces/{workspace}/views/{view_id}',response_model=ViewRead,operation_id='getView')
def get_view(request: Request,actor: A,workspace: str,view_id: str):
    request.app.state.workspaces.get(workspace)
    with request.app.state.database.session(actor.tenant_id) as db:
        return ViewRead.model_validate(views.get_view(db,actor,workspace,view_id))

@router.get('/entities',response_model=list[EntityDefinition],operation_id='listEntityDefinitions')
def entity_definitions(request: Request, actor: A):
    actor.require('read')
    return request.app.state.entities.definitions()

@router.get('/search',response_model=list[GlobalSearchResult],operation_id='globalSearch')
def global_search(request: Request, actor: A, q: str = Query(..., min_length=1, max_length=200), limit: int = Query(50, ge=1, le=100)):
    with request.app.state.database.session(actor.tenant_id) as db:
        return search.global_search(db, actor, request.app.state.entities, q, limit)

@router.post('/entities/{entity_key}/bulk-update',response_model=EntityBulkUpdateResult,operation_id='bulkUpdateEntityRecords')
def bulk_update_entity_records(request:Request,actor:A,entity_key:str,data:EntityBulkUpdateRequest,idempotency_key:str=Header(...)):
    entity=request.app.state.entities.definition(entity_key)
    workspace=request.app.state.workspaces.get(entity.workspace)
    editable={field.key for field in workspace.fields if not field.read_only}
    invalid=sorted(set(data.patch)-editable)
    if invalid:
        raise AppError(422,'bulk_field_readonly','Bulk update includes unsupported or read-only fields.',{'fields':invalid})
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        result=execute_once(db,actor,idempotency_key,f'entities.{entity_key}.bulk_update',data.model_dump(),lambda:{'updated':[row.model_dump(mode='json') for row in request.app.state.entities.bulk_update(db,actor,entity_key,data.targets,data.patch)]})
        return EntityBulkUpdateResult.model_validate(result)

@router.get('/entities/{entity_key}',response_model=EntityDefinition,operation_id='getEntityDefinition')
def entity_definition(request: Request,actor: A,entity_key: str):
    actor.require('read')
    return request.app.state.entities.definition(entity_key)

@router.get('/entities/{entity_key}/search',response_model=list[EntityReference],operation_id='searchEntityRecords')
def search_entity_records(request: Request,actor: A,entity_key: str,q: str=Query('',max_length=200),limit: int=Query(20,ge=1,le=100)):
    with request.app.state.database.session(actor.tenant_id) as db:
        return request.app.state.entities.search(db,entity_key,q,limit)

@router.get('/relationships/definitions',response_model=list[RelationshipDefinition],operation_id='listRelationshipDefinitions')
def relationship_definitions(request: Request,actor: A):
    actor.require('read')
    return request.app.state.entities.relationship_definitions()

@router.get('/relationships',response_model=list[RelationshipRead],operation_id='listRelationships')
def list_relationships(request: Request,actor: A,entity: str=Query(...,max_length=40),record_id: str=Query(...,max_length=64),include_archived: bool=False):
    with request.app.state.database.session(actor.tenant_id) as db:
        return relationships.list_for_record(db,actor,request.app.state.entities,entity,record_id,include_archived=include_archived)

@router.get('/relationships/graph',response_model=list[RelationshipRead],operation_id='listRelationshipGraph')
def relationship_graph(request: Request,actor: A,entity: str=Query(...,max_length=40),include_archived: bool=False,limit: int=Query(500,ge=1,le=1000)):
    with request.app.state.database.session(actor.tenant_id) as db:
        return relationships.list_for_entity(db,actor,request.app.state.entities,entity,include_archived=include_archived,limit=limit)

@router.get('/relationships/explore',response_model=list[RelationshipRead],operation_id='exploreRelationships')
def explore_relationships(request:Request,actor:A,entity:str=Query(...,max_length=40),record_id:str=Query(...,max_length=64),kind:str|None=Query(default=None,max_length=20),direction:str=Query('both',pattern='^(both|incoming|outgoing)$'),depth:int=Query(1,ge=1,le=8),limit:int=Query(200,ge=1,le=1000)):
    with request.app.state.database.session(actor.tenant_id) as db:
        return relationships.explore(db,actor,request.app.state.entities,entity,record_id,kind=kind,direction=direction,depth=depth,limit=limit)

@router.get('/relationships/{explorer}/explore',response_model=list[RelationshipRead],operation_id='namedRelationshipExplorer')
def named_relationship_explorer(request:Request,actor:A,explorer:str,entity:str=Query(...,max_length=40),record_id:str=Query(...,max_length=64),depth:int=Query(2,ge=1,le=8),limit:int=Query(200,ge=1,le=1000)):
    mapping={'related':(None,'both'),'backlinks':(None,'incoming'),'dependencies':('dependency','outgoing'),'impact':('dependency','incoming'),'connections':('connection','both')}
    if explorer not in mapping: raise AppError(404,'explorer_missing','Relationship explorer is not available.')
    kind,direction=mapping[explorer]
    with request.app.state.database.session(actor.tenant_id) as db:
        return relationships.explore(db,actor,request.app.state.entities,entity,record_id,kind=kind,direction=direction,depth=depth,limit=limit)

@router.post('/relationships',response_model=RelationshipRead,status_code=201,operation_id='createRelationship')
def create_relationship(request: Request,actor: A,data: RelationshipCreate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return relationships.create(db,actor,request.app.state.entities,data)

@router.put('/relationships/{relationship_id}',response_model=RelationshipRead,operation_id='updateRelationship')
def update_relationship(request: Request,actor: A,relationship_id: str,data: RelationshipUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return relationships.update_metadata(db,actor,request.app.state.entities,relationship_id,data)

@router.post('/relationships/{relationship_id}/lifecycle/{action}',response_model=RelationshipRead,operation_id='relationshipLifecycle')
def relationship_lifecycle(request: Request,actor: A,relationship_id: str,action: str,data: RevisionInput):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        return relationships.lifecycle(db,actor,request.app.state.entities,relationship_id,data.revision,action)

@router.get('/relationships/{relationship_id}/history',response_model=list[AuditRead],operation_id='relationshipHistory')
def relationship_history(request: Request,actor: A,relationship_id: str):
    with request.app.state.database.session(actor.tenant_id) as db:
        return relationships.history(db,actor,relationship_id)

# Generic platform services. These endpoints expose bounded administration/read
# surfaces; feature code enqueues jobs/emits events through the platform services.
from app.platform.schemas import JobRead, EventRead, NotificationRead, NotificationPreferenceRead, NotificationPreferenceUpdate, FeatureFlagRead, FeatureFlagWrite, WebhookDeliveryRead, WebhookEndpointRead, WebhookEndpointWrite, TeamCreate, TeamRead, TeamMemberWrite, TeamMemberRead, CommentCreate, CommentRead
from app.platform import jobs as platform_jobs, events as platform_events, notifications as platform_notifications, feature_flags as platform_flags, webhooks as platform_webhooks, teams as platform_teams, comments as platform_comments

@router.get('/records/{entity}/{record_id}/comments',response_model=list[CommentRead],operation_id='listRecordComments')
def list_record_comments(request:Request,actor:A,entity:str,record_id:str):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_comments.list_comments(db,actor,entity,record_id,request.app.state.entities)

@router.post('/records/{entity}/{record_id}/comments',response_model=CommentRead,status_code=201,operation_id='createRecordComment')
def create_record_comment(request:Request,actor:A,entity:str,record_id:str,data:CommentCreate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_comments.create_comment(db,actor,entity,record_id,data,request.app.state.entities)

@router.delete('/records/comments/{comment_id}',status_code=204,operation_id='deleteRecordComment')
def delete_record_comment(request:Request,actor:A,comment_id:str):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:platform_comments.delete_comment(db,actor,comment_id,request.app.state.entities)
    return Response(status_code=204)

@router.get('/records/{entity}/{record_id}/attachments',response_model=list[AttachmentRead],operation_id='listRecordAttachments')
def list_record_attachments(request:Request,actor:A,entity:str,record_id:str):
    with request.app.state.database.session(actor.tenant_id) as db:
        reference=request.app.state.entities.resolve(db,entity,record_id)
        rows=db.scalars(select(Attachment).where(Attachment.workspace==reference.workspace,Attachment.entity_id==record_id).order_by(Attachment.created_at,Attachment.id)).all()
        return [AttachmentRead.model_validate(row) for row in rows]

@router.post('/records/{entity}/{record_id}/attachments',response_model=AttachmentRead,status_code=201,operation_id='addRecordAttachment')
def add_record_attachment(request:Request,actor:A,entity:str,record_id:str,data:AttachmentUpload):
    if not request.app.state.settings.attachment_upload_mode or request.app.state.settings.attachment_upload_mode == 'disabled':
        raise AppError(503,'attachments_disabled','Attachment uploads are disabled by deployment policy.')
    with write_transaction(request.app.state.database,actor.tenant_id) as db:
        reference=request.app.state.entities.resolve(db,entity,record_id)
        if reference.archived:raise AppError(409,'archived_readonly','Restore this record before adding files.')
        return attach(db,actor,reference.workspace,record_id,data,tenant_id=actor.tenant_id,storage=request.app.state.object_storage,scanner=request.app.state.malware_scanner,upload_mode=request.app.state.settings.attachment_upload_mode,registry=request.app.state.entities)

@router.get('/records/{entity}/{record_id}/attachments/{attachment_id}',operation_id='downloadRecordAttachment')
def download_record_attachment(request:Request,actor:A,entity:str,record_id:str,attachment_id:str):
    from urllib.parse import quote
    with request.app.state.database.session(actor.tenant_id) as db:
        reference=request.app.state.entities.resolve(db,entity,record_id)
        row=db.get(Attachment,attachment_id)
        if row is None or row.workspace!=reference.workspace or row.entity_id!=record_id:raise AppError(404,'attachment_missing','Attachment is not available.')
        content=read_content(row,tenant_id=actor.tenant_id,storage=request.app.state.object_storage)
        return Response(content,media_type='application/octet-stream',headers={'Content-Disposition':f"attachment; filename*=UTF-8''{quote(row.filename,safe='')}",'X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; sandbox"})

@router.get('/teams',response_model=list[TeamRead],operation_id='listWorkspaceTeams')
def list_workspace_teams(request:Request,actor:A):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_teams.list_teams(db,actor)

@router.post('/teams',response_model=TeamRead,status_code=201,operation_id='createWorkspaceTeam')
def create_workspace_team(request:Request,actor:A,data:TeamCreate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_teams.create_team(db,actor,data)

@router.post('/teams/{team_id}/members',response_model=TeamMemberRead,operation_id='addWorkspaceTeamMember')
def add_workspace_team_member(request:Request,actor:A,team_id:str,data:TeamMemberWrite):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_teams.add_member(db,actor,team_id,data)

@router.get('/jobs',response_model=list[JobRead],operation_id='listDurableJobs')
def list_durable_jobs(request:Request,actor:A,status:str|None=Query(default=None,max_length=20),limit:int=Query(100,ge=1,le=200)):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_jobs.list_jobs(db,actor,status=status,limit=limit)

@router.post('/jobs/{job_id}/cancel',response_model=JobRead,operation_id='cancelDurableJob')
def cancel_durable_job(request:Request,actor:A,job_id:str):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_jobs.cancel(db,actor,job_id)

@router.get('/events',response_model=list[EventRead],operation_id='listPlatformEvents')
def list_platform_events(request:Request,actor:A,after:int=Query(0,ge=0),topic:list[str]|None=Query(default=None),limit:int=Query(100,ge=1,le=500)):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_events.list_events(db,actor,after=after,topics=topic,limit=limit)

@router.get('/notifications',response_model=list[NotificationRead],operation_id='listNotifications')
def list_notifications(request:Request,actor:A,unread_only:bool=False,limit:int=Query(100,ge=1,le=200)):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_notifications.list_mine(db,actor,unread_only=unread_only,limit=limit)

@router.post('/notifications/{notification_id}/read',response_model=NotificationRead,operation_id='markNotificationRead')
def mark_notification_read(request:Request,actor:A,notification_id:str):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_notifications.mark_read(db,actor,notification_id)

@router.post('/notifications/read-all',operation_id='markAllNotificationsRead')
def mark_all_notifications_read(request:Request,actor:A):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return {'updated':platform_notifications.mark_all_read(db,actor)}

@router.post('/notifications/{notification_id}/dismiss',response_model=NotificationRead,operation_id='dismissNotification')
def dismiss_notification(request:Request,actor:A,notification_id:str):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_notifications.dismiss(db,actor,notification_id)

@router.get('/notification-preferences',response_model=list[NotificationPreferenceRead],operation_id='listNotificationPreferences')
def list_notification_preferences(request:Request,actor:A):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_notifications.list_preferences(db,actor)

@router.put('/notification-preferences/{kind}',response_model=NotificationPreferenceRead,operation_id='setNotificationPreference')
def set_notification_preference(request:Request,actor:A,kind:str,data:NotificationPreferenceUpdate):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_notifications.set_preference(db,actor,kind,data.enabled,data.revision)

@router.get('/feature-flags',response_model=list[FeatureFlagRead],operation_id='listFeatureFlags')
def list_feature_flags(request:Request,actor:A):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_flags.list_flags(db,actor)

@router.put('/feature-flags/{key}',response_model=FeatureFlagRead,operation_id='setFeatureFlag')
def set_feature_flag(request:Request,actor:A,key:str,data:FeatureFlagWrite):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_flags.set_flag(db,actor,key,data)

@router.get('/webhooks',response_model=list[WebhookEndpointRead],operation_id='listWebhookEndpoints')
def list_webhook_endpoints(request:Request,actor:A):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_webhooks.list_endpoints(db,actor)

@router.post('/webhooks',response_model=WebhookEndpointRead,status_code=201,operation_id='createWebhookEndpoint')
def create_webhook_endpoint(request:Request,actor:A,data:WebhookEndpointWrite):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_webhooks.upsert(db,actor,request.app.state.settings,None,data)

@router.put('/webhooks/{endpoint_id}',response_model=WebhookEndpointRead,operation_id='updateWebhookEndpoint')
def update_webhook_endpoint(request:Request,actor:A,endpoint_id:str,data:WebhookEndpointWrite):
    with write_transaction(request.app.state.database,actor.tenant_id) as db:return platform_webhooks.upsert(db,actor,request.app.state.settings,endpoint_id,data)

@router.get('/webhooks/{endpoint_id}/deliveries',response_model=list[WebhookDeliveryRead],operation_id='listWebhookDeliveries')
def list_webhook_deliveries(request:Request,actor:A,endpoint_id:str,limit:int=Query(100,ge=1,le=200)):
    with request.app.state.database.session(actor.tenant_id) as db:return platform_webhooks.list_deliveries(db,actor,endpoint_id,limit)

@router.get('/runtime-diagnostics',operation_id='runtimeDiagnostics')
def runtime_diagnostics(request:Request,actor:A):
    actor.require('admin')
    return {'environment':request.app.state.settings.environment,'profile':request.app.state.settings.profile,'deployment_id':request.app.state.settings.deployment_id,'instance_id':request.app.state.instance_id,'webhook_allowed_hosts':len(request.app.state.settings.webhook_allowed_hosts),'docs_enabled':bool(request.app.docs_url)}

from app.platform.schemas import MemberRead, MemberWrite, PermissionMatrixRead

def _admin_members(db,actor:A):
    actor.require('admin')
    return list(db.scalars(select(Membership).where(Membership.tenant_id==actor.tenant_id).order_by(Membership.user_id)).all())

def _require_role(request:Request,role:str):
    if role not in request.app.state.policy.roles:raise AppError(422,'invalid_role','Role is not defined by the application policy.')

def _admin_count(rows):return sum(1 for row in rows if row.role=='admin')

@router.get('/admin/members',response_model=list[MemberRead],operation_id='listMembers')
def list_members(request:Request,actor:A):
    with request.app.state.database.session() as db:return [MemberRead(user_id=row.user_id,role=row.role) for row in _admin_members(db,actor)]

@router.post('/admin/members',response_model=MemberRead,status_code=201,operation_id='createMember')
def create_member(request:Request,actor:A,data:MemberWrite):
    actor.require('admin');_require_role(request,data.role)
    with request.app.state.database.session() as db:
        if db.get(Membership,(actor.tenant_id,data.user_id)):raise AppError(409,'member_exists','User is already a member of this tenant.')
        row=Membership(tenant_id=actor.tenant_id,user_id=data.user_id,role=data.role);db.add(row);db.commit();return MemberRead(user_id=row.user_id,role=row.role)

@router.put('/admin/members/{user_id}',response_model=MemberRead,operation_id='updateMember')
def update_member(request:Request,actor:A,user_id:str,data:MemberWrite):
    actor.require('admin');_require_role(request,data.role)
    if data.user_id!=user_id:raise AppError(422,'member_identity_immutable','Member user ID cannot be changed.')
    with request.app.state.database.session() as db:
        rows=_admin_members(db,actor);row=db.get(Membership,(actor.tenant_id,user_id))
        if not row:raise AppError(404,'member_missing','Member is not available.')
        if row.role=='admin' and data.role!='admin' and _admin_count(rows)<=1:raise AppError(409,'last_admin','At least one administrator must remain.')
        row.role=data.role;db.commit();return MemberRead(user_id=row.user_id,role=row.role)

@router.delete('/admin/members/{user_id}',status_code=204,operation_id='deleteMember')
def delete_member(request:Request,actor:A,user_id:str):
    actor.require('admin')
    with request.app.state.database.session() as db:
        rows=_admin_members(db,actor);row=db.get(Membership,(actor.tenant_id,user_id))
        if not row:raise AppError(404,'member_missing','Member is not available.')
        if row.role=='admin' and _admin_count(rows)<=1:raise AppError(409,'last_admin','At least one administrator must remain.')
        db.delete(row);db.commit()
    return Response(status_code=204)

@router.get('/admin/permissions',response_model=PermissionMatrixRead,operation_id='permissionMatrix')
def permission_matrix(request:Request,actor:A):
    actor.require('admin');return PermissionMatrixRead(roles={role:sorted(permissions) for role,permissions in request.app.state.policy.roles.items()})
