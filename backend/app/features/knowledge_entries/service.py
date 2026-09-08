from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import KnowledgeEntrie
from .schemas import KnowledgeEntrieCreate,KnowledgeEntrieRead,KnowledgeEntriePage,KnowledgeEntrieBulkRequest
WORKSPACE='knowledge_entries'
SORTS={'title':KnowledgeEntrie.title,'entry_type':KnowledgeEntrie.entry_type,'status':KnowledgeEntrie.status,'criticality':KnowledgeEntrie.criticality,'owner':KnowledgeEntrie.owner,'review_state':KnowledgeEntrie.review_state,'next_review_at':KnowledgeEntrie.next_review_at,'updated_at':KnowledgeEntrie.updated_at,'created_at':KnowledgeEntrie.created_at,'created_by':KnowledgeEntrie.created_by,'revision':KnowledgeEntrie.revision}
CRUD=RevisionCrudService(model=KnowledgeEntrie,create_schema=KnowledgeEntrieCreate,read_schema=KnowledgeEntrieRead,workspace=WORKSPACE,not_found_label='Knowledge Entry')
QUERY=EntityQueryService(model=KnowledgeEntrie,read_schema=KnowledgeEntrieRead,sorts=SORTS,search_columns=(KnowledgeEntrie.title,KnowledgeEntrie.owner,KnowledgeEntrie.content,),filters={'entry_type':(KnowledgeEntrie.entry_type,('runbook', 'procedure', 'troubleshooting', 'architecture_note', 'lesson', 'standard', 'faq')),'status':(KnowledgeEntrie.status,('draft', 'published', 'archived_reference')),'criticality':(KnowledgeEntrie.criticality,('standard', 'critical')),'review_state':(KnowledgeEntrie.review_state,('needs_review', 'verified', 'stale', 'deprecated', 'emergency_only'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=KnowledgeEntriePage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:KnowledgeEntrieBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
