from __future__ import annotations
from datetime import datetime, timedelta, timezone
import os
import pytest
import time
from app.platform.security import Actor
from app.platform.schemas import NotificationCreate
from app.platform import events, jobs, notifications, webhooks
from app.platform.errors import AppError


def actor(env,user='alice',permissions=frozenset({'read','write','admin','restore'})):
    return Actor(user,env['tenant'],'admin','test-request',permissions)


def test_feature_flags_are_revision_safe_and_admin_only(env,client):
    created=client.put('/api/v1/feature-flags/new-dashboard',json={'enabled':True,'description':'Progressive rollout','rules':{}})
    assert created.status_code==200 and created.json()['revision']==1 and created.json()['enabled'] is True
    assert client.get('/api/v1/feature-flags').json()[0]['key']=='new-dashboard'
    stale=client.put('/api/v1/feature-flags/new-dashboard',json={'enabled':False,'description':'','rules':{},'revision':9})
    assert stale.status_code==409
    updated=client.put('/api/v1/feature-flags/new-dashboard',json={'enabled':False,'description':'','rules':{},'revision':1})
    assert updated.status_code==200 and updated.json()['revision']==2
    assert env['client']('bob').put('/api/v1/feature-flags/x',json={'enabled':True}).status_code==403


def test_notification_preferences_and_private_inbox(env,client):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        made=notifications.create(session,a,NotificationCreate(user_id='alice',kind='release.ready',title='Release ready'))
        assert made is not None;session.commit()
    inbox=client.get('/api/v1/notifications').json();assert len(inbox)==1 and inbox[0]['title']=='Release ready'
    assert env['client']('bob').get('/api/v1/notifications').json()==[]
    marked=client.post('/api/v1/notifications/'+inbox[0]['id']+'/read');assert marked.status_code==200 and marked.json()['read_at']
    pref=client.put('/api/v1/notification-preferences/release.ready',json={'enabled':False});assert pref.status_code==200 and pref.json()['revision']==1
    assert client.get('/api/v1/notification-preferences').json()[0]['enabled'] is False
    assert client.post('/api/v1/notifications/read-all').json()=={'updated':0}
    dismissed=client.post('/api/v1/notifications/'+inbox[0]['id']+'/dismiss');assert dismissed.status_code==200 and dismissed.json()['dismissed_at']
    assert client.get('/api/v1/notifications').json()==[]
    with env['db'].session(env['tenant']) as session:
        assert notifications.create(session,a,NotificationCreate(user_id='alice',kind='release.ready',title='Suppressed')) is None


def test_events_are_ordered_filterable_and_tenant_scoped(env,client):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        one=events.emit(session,a,'record.updated',{'revision':2},entity_type='work_items',entity_id='A')
        two=events.emit(session,a,'record.archived',{'revision':3},entity_type='work_items',entity_id='A')
        session.commit()
    feed=client.get('/api/v1/events').json();assert [row['topic'] for row in feed]==['record.updated','record.archived']
    assert client.get('/api/v1/events',params={'after':one.sequence}).json()[0]['event_id']==two.event_id
    filtered=client.get('/api/v1/events',params=[('topic','record.archived')]).json();assert len(filtered)==1
    assert env['client']('carol').get('/api/v1/events',headers={'X-Tenant-Id':env['other']}).json()==[]


def test_durable_job_leasing_retry_and_cancel(env,client):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        first=jobs.enqueue(session,a,'test.echo',{'value':3},max_attempts=2);session.commit();job_id=first.id
    with env['db'].session(env['tenant']) as session:
        result=jobs.run_once(session,'worker-1',{'test.echo':lambda payload:{'value':payload['value']*2}});session.commit()
        assert result and result.id==job_id and result.status=='succeeded' and result.result=={'value':6}
        queued=jobs.enqueue(session,a,'test.missing',{},max_attempts=1);session.commit();queued_id=queued.id
    with env['db'].session(env['tenant']) as session:
        result=jobs.run_once(session,'worker-2',{});session.commit();assert result and result.id==queued_id and result.status=='failed'
        cancel=jobs.enqueue(session,a,'test.echo',{});session.commit();cancel_id=cancel.id
    cancelled=client.post(f'/api/v1/jobs/{cancel_id}/cancel');assert cancelled.status_code==200 and cancelled.json()['status']=='cancelled'
    assert env['client']('bob').get('/api/v1/jobs').status_code==403

def test_job_heartbeat_and_fencing_reject_stale_worker(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.fenced',{});session.commit()
    with env['db'].session(env['tenant']) as session:
        first=jobs.lease_next(session,'worker-a',lease_seconds=30);assert first and first.id==queued.id and first.fence_token
        token=first.fence_token;jobs.heartbeat(session,first,'worker-a',token,lease_seconds=60);session.commit()
    with env['db'].session(env['tenant']) as session:
        row=session.get(type(first),queued.id)
        with pytest.raises(AppError):jobs.finish(session,row,'worker-b',token,result={})
        with pytest.raises(AppError):jobs.heartbeat(session,row,'worker-a','wrong-fence',lease_seconds=60)
        jobs.finish(session,row,'worker-a',token,result={'ok':True});session.commit()


def test_expired_job_lease_can_be_reclaimed_by_new_worker(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.reclaim',{});session.commit()
    with env['db'].session(env['tenant']) as session:
        first=jobs.lease_next(session,'worker-a',lease_seconds=30);assert first and first.id==queued.id
        first.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);session.commit()
    with env['db'].session(env['tenant']) as session:
        replacement=jobs.lease_next(session,'worker-b',lease_seconds=30)
        assert replacement and replacement.id==queued.id and replacement.lease_owner=='worker-b'


def test_handler_exception_retries_then_final_fails(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.always-fails',{},max_attempts=2);session.commit()
    def fail(_payload):
        raise RuntimeError('deterministic failure')
    first=jobs.process_one(env['db'],env['tenant'],'worker-a',{'test.always-fails':fail},lease_seconds=5,heartbeat_interval=.05)
    assert first and first.status=='retrying' and first.attempts==1
    from app.platform.models import DurableJob
    with env['db'].session(env['tenant']) as session:
        row=session.get(DurableJob,queued.id);row.run_after=datetime.now(timezone.utc)-timedelta(seconds=1);session.commit()
    second=jobs.process_one(env['db'],env['tenant'],'worker-a',{'test.always-fails':fail},lease_seconds=5,heartbeat_interval=.05)
    assert second and second.status=='failed' and second.attempts==2


def test_webhook_definition_is_allowlisted_revision_safe_and_secret_ref_only(env,monkeypatch):
    client=env['client'](webhook_allowed_hosts=['hooks.example.com'])
    payload={'name':'Ops hook','url':'https://hooks.example.com/events','topics':['record.updated'],'secret_ref':'OPS_HOOK','enabled':True}
    created=client.post('/api/v1/webhooks',json=payload);assert created.status_code==201,created.text
    body=created.json();assert 'secret' not in body and body['secret_ref']=='OPS_HOOK'
    assert client.post('/api/v1/webhooks',json={**payload,'url':'https://127.0.0.1/internal'}).status_code==422
    assert client.post('/api/v1/webhooks',json={**payload,'url':'http://hooks.example.com/events'}).status_code==422
    assert client.put('/api/v1/webhooks/'+body['id'],json={**payload,'revision':9}).status_code==409
    monkeypatch.setenv('BASE_WEBHOOK_SECRET_OPS_HOOK','x'*40)
    from app.platform.models import WebhookEndpoint
    with env['db'].session(env['tenant']) as session:
        row=session.get(WebhookEndpoint,body['id']);raw,headers=webhooks.delivery_request(row,'record.updated',{'id':'1'},1700000000)
    assert raw.startswith(b'{') and headers['X-Golden-Signature'].startswith('sha256=') and 'x'*20 not in raw.decode()


def test_webhook_settings_reject_unsafe_hosts():
    from app.platform.settings import Settings
    with pytest.raises(ValueError):Settings(environment='test',profile='development',webhook_allowed_hosts=['localhost'])
    with pytest.raises(ValueError):Settings(environment='test',profile='development',webhook_allowed_hosts=['hooks.example.com:8443'])

class _WebhookResponse:
    status_code=204
class _WebhookClient:
    def __init__(self):self.calls=[]
    def post(self,url,content,headers):self.calls.append((url,content,headers));return _WebhookResponse()

def test_revision_events_enqueue_and_deliver_allowlisted_webhook(env,monkeypatch):
    client=env['client'](webhook_allowed_hosts=['hooks.example.com'])
    hook=client.post('/api/v1/webhooks',json={'name':'Record hook','url':'https://hooks.example.com/events','topics':['work_items.create'],'secret_ref':'RECORD_HOOK','enabled':True})
    assert hook.status_code==201,hook.text
    created=client.post('/api/v1/work-items',json={'title':'Webhook fanout'})
    assert created.status_code==201,created.text
    events_feed=client.get('/api/v1/events',params=[('topic','work_items.create')]).json();assert len(events_feed)==1
    queue=client.get('/api/v1/jobs').json();delivery=[row for row in queue if row['job_type']=='webhook.deliver'];assert len(delivery)==1
    monkeypatch.setenv('BASE_WEBHOOK_SECRET_RECORD_HOOK','s'*40)
    fake=_WebhookClient()
    from app.platform import webhooks as webhook_service
    with env['db'].session(env['tenant']) as session:
        result=webhook_service.deliver(session,client.app.state.settings,hook.json()['id'],events_feed[0]['event_id'],client=fake)
        session.commit()
    assert result['status_code']==204 and len(fake.calls)==1
    url,body,headers=fake.calls[0];assert url=='https://hooks.example.com/events' and b'Webhook fanout' not in body
    assert headers['X-Golden-Signature'].startswith('sha256=')
    history=client.get('/api/v1/webhooks/'+hook.json()['id']+'/deliveries')
    assert history.status_code==200 and history.json()[0]['status']=='delivered' and history.json()[0]['attempts']==1

class _FailedWebhookResponse:
    status_code=503

def test_webhook_delivery_history_records_retryable_failure(env,monkeypatch):
    client=env['client'](webhook_allowed_hosts=['hooks.example.com'])
    hook=client.post('/api/v1/webhooks',json={'name':'Retry hook','url':'https://hooks.example.com/events','topics':['record.updated'],'secret_ref':'RETRY_HOOK','enabled':True})
    monkeypatch.setenv('BASE_WEBHOOK_SECRET_RETRY_HOOK','r'*40)
    from app.platform import webhooks as webhook_service
    with env['db'].session(env['tenant']) as session:
        event=events.emit(session,actor(env),'record.updated',{'id':'retry'})
        session.commit();event_id=event.event_id
    with env['db'].session(env['tenant']) as session:
        with pytest.raises(RuntimeError):webhook_service.deliver(session,client.app.state.settings,hook.json()['id'],event_id,client=type('FailingClient',(),{'post':lambda self,*args,**kwargs:_FailedWebhookResponse()})())
        session.commit()
    history=client.get('/api/v1/webhooks/'+hook.json()['id']+'/deliveries').json()
    assert history[0]['status']=='retrying' and history[0]['response_status']==503 and history[0]['last_error']=='non_success_response'

def test_process_one_releases_database_lock_before_handler(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.reentrant',{'ok':True});session.commit()
    observed=[]
    def handler(payload):
        # This independent read/write-capable session must be possible while the
        # handler runs; the job lease transaction has already committed.
        with env['db'].session(env['tenant']) as session:
            observed.append(session.execute(__import__('sqlalchemy').text('select count(*) from durable_jobs')).scalar_one())
        return {'observed':observed[-1],**payload}
    result=jobs.process_one(env['db'],env['tenant'],'worker-reentrant',{'test.reentrant':handler})
    assert result and result.id==queued.id and result.status=='succeeded' and observed==[1]


def test_process_one_renews_long_handler_lease(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.long',{});session.commit();job_id=queued.id
    def handler(_payload):
        time.sleep(1.2)
        with env['db'].session(env['tenant']) as session:
            assert jobs.lease_next(session,'worker-b',lease_seconds=1) is None
        return {'renewed':True}
    result=jobs.process_one(env['db'],env['tenant'],'worker-a',{'test.long':handler},lease_seconds=1,heartbeat_interval=.05)
    assert result and result.id==job_id and result.status=='succeeded' and result.result=={'renewed':True}, result


def test_process_one_lost_fence_cannot_finalize_handler_result(env):
    a=actor(env)
    with env['db'].session(env['tenant']) as session:
        queued=jobs.enqueue(session,a,'test.reclaimed',{});session.commit();job_id=queued.id
    def handler(_payload):
        from datetime import timedelta
        from app.platform.models import DurableJob
        with env['db'].session(env['tenant']) as session:
            row=session.get(DurableJob,job_id);row.lease_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);session.commit()
        with env['db'].session(env['tenant']) as session:
            replacement=jobs.lease_next(session,'worker-b',lease_seconds=5);assert replacement and replacement.id==job_id;session.commit()
        return {'stale':True}
    result=jobs.process_one(env['db'],env['tenant'],'worker-a',{'test.reclaimed':handler},lease_seconds=5,heartbeat_interval=.03)
    assert result and result.id==job_id and result.status=='running' and result.lease_owner=='worker-b',result

def test_member_admin_api_and_last_admin_protection(env,client):
    members=client.get('/api/v1/admin/members');assert members.status_code==200 and {row['user_id'] for row in members.json()}=={'alice','bob','victor'}
    matrix=client.get('/api/v1/admin/permissions');assert matrix.status_code==200 and 'admin' in matrix.json()['roles']
    created=client.post('/api/v1/admin/members',json={'user_id':'new.editor','role':'editor'});assert created.status_code==201
    updated=client.put('/api/v1/admin/members/new.editor',json={'user_id':'new.editor','role':'viewer'});assert updated.status_code==200 and updated.json()['role']=='viewer'
    assert client.put('/api/v1/admin/members/alice',json={'user_id':'alice','role':'editor'}).status_code==409
    assert client.delete('/api/v1/admin/members/alice').status_code==409
    assert client.delete('/api/v1/admin/members/new.editor').status_code==204
    assert env['client']('bob').get('/api/v1/admin/members').status_code==403
