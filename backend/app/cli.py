from __future__ import annotations
import argparse
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select
from app.platform.settings import Settings
from app.platform.database import Database
from app.platform.models import Tenant
from app.platform.provision import provision,add_member
from app.platform.migrations import migrate
from app.platform.backup import snapshot,restore
from app.profiles.company.storage_probe import probe
from app.tooling.work_items import create_work_item_direct
from app.features.work_items.schemas import WorkItemCreate


def _deliver_webhook_job(database,settings,tenant_id,payload):
    from app.platform.webhooks import deliver
    with database.session(tenant_id) as session:
        return deliver(session,settings,str(payload.get('endpoint_id','')),str(payload.get('event_id','')))


def _assert_operator_safe(settings: Settings) -> None:
    """Validate production qualification without pretending maintenance has a scanner.

    These commands do not accept uploads or start the ASGI request surface. The
    application startup and ``preflight`` continue to require an actual scanner
    whenever ``scanner_required`` is selected.
    """
    settings.assert_maintenance_safe()

def main():
    parser=argparse.ArgumentParser(description='Golden operator tools. Never run against live data without the documented maintenance procedure.')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('provision');p.add_argument('--tenant',required=True);p.add_argument('--admin',required=True)
    p=commands.add_parser('add-member');p.add_argument('--tenant-id',required=True);p.add_argument('--user',required=True);p.add_argument('--role',required=True,choices=['admin','editor','viewer'])
    p=commands.add_parser('migrate');p.add_argument('--maintenance',required=True,choices=['APP-STOPPED'])
    p=commands.add_parser('backup');p.add_argument('--output',type=Path,required=True);p.add_argument('--maintenance',required=True,choices=['APP-STOPPED'])
    p=commands.add_parser('restore');p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p=commands.add_parser('doctor-storage');p.add_argument('--scratch-parent',type=Path,required=True)
    p=commands.add_parser('run-jobs');p.add_argument('--once',action='store_true');p.add_argument('--worker-id',default='operator-worker')
    commands.add_parser('preflight')
    commands.add_parser('seed-demo')
    args=parser.parse_args();settings=Settings();database=Database(settings)
    try:
        if args.command=='preflight':
            # The operator CLI has no injected scanner provider.  Treat the
            # scanner-required mode as no-op here so production preflight
            # cannot accidentally approve a process that would fail closed at
            # application startup.
            errors=settings.production_errors(scanner_is_noop=settings.attachment_upload_mode=='scanner_required')
            if settings.environment!='production':errors.append('Preflight must be run with BASE_ENVIRONMENT=production.')
            print(json.dumps({'ready':not errors,'errors':errors},indent=2));return 1 if errors else 0
        if args.command=='doctor-storage':
            result=probe(args.scratch_parent);print(json.dumps(result,indent=2));return 0 if result['diagnostic_pass'] else 1
        if args.command=='run-jobs':
            _assert_operator_safe(settings)
            from app.platform.jobs import process_one
            from app.platform.webhooks import deliver as deliver_webhook
            processed=0
            with database.session() as session: tenant_ids=list(session.scalars(select(Tenant.id).where(Tenant.active.is_(True))))
            for tenant_id in tenant_ids:
                handlers={'webhook.deliver':lambda payload,tenant_id=tenant_id: _deliver_webhook_job(database,settings,tenant_id,payload)}
                while True:
                    row=process_one(database,tenant_id,args.worker_id,handlers)
                    if row is None:break
                    processed+=1;print(json.dumps({'tenant_id':tenant_id,'job_id':row.id,'job_type':row.job_type,'status':row.status}))
                    if args.once:break
            print(json.dumps({'processed':processed,'worker_id':args.worker_id}));return 0
        if args.command=='restore':print(restore(args.snapshot,args.target));return 0
        _assert_operator_safe(settings)
        if args.command=='provision':print(provision(database,args.tenant,args.admin))
        elif args.command=='add-member':add_member(database,args.tenant_id,args.user,args.role)
        elif args.command=='migrate':
            migrate(database)
            with database.session() as session:ids=list(session.scalars(select(Tenant.id)))
            for tenant_id in ids:migrate(database,tenant_id)
        elif args.command=='backup':print(snapshot(database.root,args.output,maintenance=args.maintenance))
        elif args.command=='seed-demo':
            if settings.environment=='production' or settings.profile=='company':raise ValueError('Demo seeding is forbidden for company or production profiles.')
            if database.path().exists():raise ValueError('Demo seeding requires a new data root. Existing data is preserved.')
            tenant_id=provision(database,'Demo workspace',settings.dev_user)
            for role in ('editor','viewer'):add_member(database,tenant_id,'demo.'+role,role)
            for title,status,priority in [('Qualify company identity','open','high'),('Confirm storage provider guarantees','in_progress','high'),('Customize application branding','open','normal'),('Review the neutral reference workflow','done','normal'),('Rehearse an isolated restore','open','normal')]:
                create_work_item_direct(database,tenant_id,WorkItemCreate(title=title,status=status,priority=priority))
            print(json.dumps({'tenant_id':tenant_id,'user':settings.dev_user}))
    finally:database.close()
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,RuntimeError,OSError) as error:
        print(str(error));raise SystemExit(1)
