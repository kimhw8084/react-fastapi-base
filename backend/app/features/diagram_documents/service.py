from app.platform.errors import AppError
from app.platform.query_service import EntityQueryService
from app.platform.revision_service import RevisionCrudService
from .models import DiagramDocument
from .schemas import DiagramDocumentCreate,DiagramDocumentRead,DiagramDocumentPage,DiagramDocumentBulkRequest
WORKSPACE='diagram_documents'
SORTS={'title':DiagramDocument.title,'diagram_type':DiagramDocument.diagram_type,'status':DiagramDocument.status,'node_count':DiagramDocument.node_count,'edge_count':DiagramDocument.edge_count,'updated_at':DiagramDocument.updated_at,'created_at':DiagramDocument.created_at,'created_by':DiagramDocument.created_by,'revision':DiagramDocument.revision}
def normalize_diagram(values):
    import math,re
    values=dict(values);nodes=values.get('nodes') or {};edges=values.get('edges') or {};viewport=values.get('viewport') or {}
    if len(nodes)>1000:raise AppError(422,'diagram_too_large','Diagram exceeds 1000 nodes.')
    if len(edges)>3000:raise AppError(422,'diagram_too_large','Diagram exceeds 3000 edges.')
    clean_nodes={}
    for node_id,node in nodes.items():
        if not isinstance(node_id,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}',node_id) or not isinstance(node,dict):raise AppError(422,'invalid_diagram_node','Each node needs a safe id and object payload.')
        label=node.get('label','Node');kind=node.get('type','entity');x=node.get('x',0);y=node.get('y',0)
        if not isinstance(label,str) or not 1<=len(label.strip())<=160:raise AppError(422,'invalid_diagram_node','Node labels must be 1-160 characters.')
        if not isinstance(kind,str) or not 1<=len(kind)<=40:raise AppError(422,'invalid_diagram_node','Node type must be 1-40 characters.')
        if isinstance(x,bool) or isinstance(y,bool) or not isinstance(x,(int,float)) or not isinstance(y,(int,float)) or not math.isfinite(x) or not math.isfinite(y) or abs(x)>100000 or abs(y)>100000:raise AppError(422,'invalid_diagram_node','Node coordinates must be finite and bounded.')
        entity=node.get('entity');record_id=node.get('record_id')
        if entity is not None and (not isinstance(entity,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,39}',entity)):raise AppError(422,'invalid_diagram_node','Node entity reference is invalid.')
        if record_id is not None and (not isinstance(record_id,str) or not 1<=len(record_id)<=64):raise AppError(422,'invalid_diagram_node','Node record reference is invalid.')
        clean_nodes[node_id]={'label':label.strip(),'type':kind,'x':float(x),'y':float(y),**({'entity':entity,'record_id':record_id} if entity and record_id else {})}
    clean_edges={}
    for edge_id,edge in edges.items():
        if not isinstance(edge_id,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}',edge_id) or not isinstance(edge,dict):raise AppError(422,'invalid_diagram_edge','Each edge needs a safe id and object payload.')
        source=edge.get('source');target=edge.get('target');label=edge.get('label','');kind=edge.get('type','flow')
        if source not in clean_nodes or target not in clean_nodes:raise AppError(422,'invalid_diagram_edge','Every edge endpoint must reference an existing node.')
        if source==target:raise AppError(422,'invalid_diagram_edge','Self-loop edges are not enabled in the base designer.')
        if not isinstance(label,str) or len(label)>160 or not isinstance(kind,str) or not 1<=len(kind)<=40:raise AppError(422,'invalid_diagram_edge','Edge label or type is invalid.')
        clean_edges[edge_id]={'source':source,'target':target,'label':label.strip(),'type':kind}
    if not isinstance(viewport,dict):raise AppError(422,'invalid_diagram_viewport','Viewport must be an object.')
    x=viewport.get('x',0);y=viewport.get('y',0);zoom=viewport.get('zoom',1)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (x,y,zoom)) or not 0.25<=zoom<=3:raise AppError(422,'invalid_diagram_viewport','Viewport position/zoom is invalid.')
    values['nodes']=clean_nodes;values['edges']=clean_edges;values['viewport']={'x':float(x),'y':float(y),'zoom':float(zoom)};values['node_count']=len(clean_nodes);values['edge_count']=len(clean_edges)
    return values
CRUD=RevisionCrudService(model=DiagramDocument,create_schema=DiagramDocumentCreate,read_schema=DiagramDocumentRead,workspace=WORKSPACE,not_found_label='Diagram',normalize_values=normalize_diagram)
QUERY=EntityQueryService(model=DiagramDocument,read_schema=DiagramDocumentRead,sorts=SORTS,search_columns=(DiagramDocument.title,DiagramDocument.notes,),filters={'diagram_type':(DiagramDocument.diagram_type,('architecture', 'workflow', 'data_flow', 'topology', 'process', 'state_machine', 'lineage')),'status':(DiagramDocument.status,('draft', 'active', 'in_review', 'retired'))})
def list_records(session,actor,*,search='',filters=None,archived=False,sort='updated_at',direction='desc',limit=50,offset=0):return QUERY.list(session,actor,page_schema=DiagramDocumentPage,search=search,filter_values=filters or {},archived=archived,sort=sort,direction=direction,limit=limit,offset=offset)
def bulk(session,actor,data:DiagramDocumentBulkRequest):
    if len({x.id for x in data.targets})!=len(data.targets):raise AppError(422,'duplicate_target','Bulk selection contains duplicate records.')
    return [CRUD.lifecycle(session,actor,x.id,x.revision,data.action) for x in data.targets]
