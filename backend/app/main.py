from __future__ import annotations
from pathlib import Path
from contextlib import asynccontextmanager
import logging
import secrets
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from uuid import uuid4
from app.platform.schemas import ErrorResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from app.platform.settings import Settings
from app.platform.policy import load_policy
from app.platform.workspace_registry import WorkspaceRegistry
from app.platform.entity_registry import EntityRegistry, load_relationship_definitions
from app.platform.configuration import load_config
from app.platform.database import Database
from app.platform.errors import AppError
from app.platform.migrations import assert_revision
from app.platform.middleware import RequestSafetyMiddleware
from app.platform.models import Tenant
from app.platform.router import router as platform_router
from app.platform.version import VERSION
from app.platform.storage import LocalFilesystemStorage
from app.platform.attachments import NoopMalwareScanner
from app.features.registry import DEFINITIONS, ENTITY_BINDINGS, ROUTERS
from app.profiles.company.identity import CompanyIdentity, DevelopmentIdentity

logger=logging.getLogger('golden')

def create_app(settings: Settings | None = None) -> FastAPI:
    settings=settings or Settings()
    application=load_config(settings.app_config)
    policy=load_policy(settings.policy_config)
    workspaces=WorkspaceRegistry(DEFINITIONS)
    relationships_path=Path(__file__).resolve().parent/'config'/'relationships.json'
    entities=EntityRegistry(ENTITY_BINDINGS,load_relationship_definitions(relationships_path))
    unknown={n.workspace for n in application.navigation}-set(DEFINITIONS)
    if unknown:raise ValueError('Unknown workspace configuration: '+', '.join(sorted(unknown)))
    database=Database(settings)
    @asynccontextmanager
    async def lifespan(app):
        settings.assert_safe()
        if settings.profile=='company':
            app.state.identity.current_user()
        yield
        database.close()
    app=FastAPI(title=application.name,version=VERSION,lifespan=lifespan,
        responses={code:{'model':ErrorResponse} for code in (400,401,403,404,409,413,415,422,429,500,503)},
        docs_url='/docs' if settings.environment!='production' and settings.enable_docs else None,
        redoc_url=None,openapi_url='/openapi.json' if settings.environment!='production' else None)
    app.state.instance_id=str(uuid4())
    app.state.settings=settings
    app.state.application=application
    app.state.policy=policy
    app.state.workspaces=workspaces
    app.state.entities=entities
    app.state.database=database
    # The adapter is tenant-scoped and stores objects outside SQLite. Company
    # deployments still fail closed through Settings qualification before use.
    app.state.object_storage=LocalFilesystemStorage(settings.data_root/'objects')
    app.state.malware_scanner=NoopMalwareScanner()
    app.state.identity=CompanyIdentity() if settings.profile=='company' else DevelopmentIdentity(settings.dev_user)
    app.state.csrf_secret=settings.csrf_secret or secrets.token_urlsafe(32)
    app.add_middleware(RequestSafetyMiddleware,settings=settings)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=settings.allowed_hosts)
    # CORS wraps safety responses too; no wildcard credentials.
    app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,
        allow_methods=['GET','POST','PUT','DELETE','OPTIONS'],allow_headers=['Content-Type','X-Tenant-Id','X-CSRF-Token','Idempotency-Key'],expose_headers=['X-Request-ID','Content-Disposition'])
    def error_response(request,status,code,message,details=None):
        return JSONResponse(status_code=status,content={'error':{'code':code,'message':message,'details':details,'request_id':getattr(request.state,'request_id','unavailable')}},headers={'Cache-Control':'no-store'})
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request:Request,error:StarletteHTTPException):
        return error_response(request,error.status_code,'http_error',str(error.detail))
    @app.exception_handler(AppError)
    async def app_error(request:Request,error:AppError):
        return error_response(request,error.status,error.code,error.message,error.details)
    @app.exception_handler(RequestValidationError)
    async def invalid(request:Request,error:RequestValidationError):
        details=[{'field':'.'.join(str(x) for x in e['loc'][1:]),'message':e['msg']} for e in error.errors()]
        return error_response(request,422,'validation_failed','Check the highlighted fields.',details)
    @app.exception_handler(OperationalError)
    async def unavailable(request:Request,error:OperationalError):
        logger.warning('Database operation unavailable; request_id=%s',getattr(request.state,'request_id','unavailable'))
        return error_response(request,503,'database_busy','Database is busy or unavailable. Try again without changing the operation key.')
    @app.exception_handler(Exception)
    async def unexpected(request:Request,error:Exception):
        logger.error('Unhandled exception type=%s request_id=%s',type(error).__name__,getattr(request.state,'request_id','unavailable'))
        return error_response(request,500,'internal_error','Unexpected server error. Contact support with the request ID.')
    @app.get('/api/v1/health',operation_id='health')
    def health():return {'alive':True,'version':VERSION}
    @app.get('/api/v1/readiness',operation_id='readiness')
    def readiness():
        try:
            settings.assert_safe();assert_revision(database)
            with database.session() as db:
                tenants=db.scalars(select(Tenant).where(Tenant.active.is_(True))).all()
            if len(tenants)>64:raise RuntimeError('Too many tenants for synchronous readiness in this release.')
            for tenant in tenants:assert_revision(database,tenant.id)
            return {'ready':True,'version':VERSION}
        except Exception:
            return JSONResponse(status_code=503,content={'ready':False,'code':'configuration_or_database_unready'})
    app.include_router(platform_router,prefix='/api/v1')
    for router in ROUTERS:
        app.include_router(router,prefix='/api/v1')
    return app

app=create_app()
