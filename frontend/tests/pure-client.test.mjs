import test from 'node:test'
import assert from 'node:assert/strict'
import {pathToFileURL} from 'node:url'
import {join} from 'node:path'
const root=process.env.BASE_SMOKE_ROOT
if(!root)throw new Error('Run through scripts/source_smoke.mjs.')
const {parseRuntime}=await import(pathToFileURL(join(root,'platform/api/runtime.js')))
const {ApiClient,ApiError}=await import(pathToFileURL(join(root,'platform/api/client.js')))
const {storageKey,readStorage,writeStorage}=await import(pathToFileURL(join(root,'platform/state/storage.js')))
const fieldDraft=await import(pathToFileURL(join(root,'platform/workspace/fieldDraft.js')))
const workspaceState=await import(pathToFileURL(join(root,'platform/workspace/workspaceState.js')))

const surface=await import(pathToFileURL(join(root,'platform/ui/surface.js')))
const surfaceStack=await import(pathToFileURL(join(root,'platform/ui/surfaceStack.js')))
const themeModel=await import(pathToFileURL(join(root,'platform/ui/theme.js')))
const commands=await import(pathToFileURL(join(root,'platform/commands/registry.js')))
const layouts=await import(pathToFileURL(join(root,'platform/layout/model.js')))
globalThis.window={location:{protocol:'https:'}}
const config={schemaVersion:1,apiBase:'',defaultTheme:'operations',titleOverride:''}
test('runtime accepts each configured visual profile',()=>{for(const defaultTheme of ['operations','clarity','minimal'])assert.equal(parseRuntime({...config,defaultTheme}).defaultTheme,defaultTheme)})
test('runtime rejects mixed content, URL credentials, paths, scripts and unknown settings',()=>{for(const patch of [{apiBase:'http://api.test'},{apiBase:'https://u:p@api.test'},{apiBase:'https://api.test/api/v1'},{apiBase:'https://api.test/'},{apiBase:'javascript:alert(1)'},{secret:'x'},{defaultTheme:'invented'}])assert.throws(()=>parseRuntime({...config,...patch}))})
test('storage keys isolate app, user, tenant and version',()=>{assert.notEqual(storageKey('a','u','t','x'),storageKey('a','v','t','x'));assert.notEqual(storageKey('a','u','t','x'),storageKey('a','u','t2','x'));assert.match(storageKey('a:b','u','t','x'),/^a%3Ab:/)})
test('corrupted or unavailable local storage is harmless',()=>{globalThis.localStorage={getItem:()=>'{broken',setItem:()=>{throw Error('quota')}};assert.equal(readStorage('k',42,Number),42);assert.equal(writeStorage('k',{}),false)})
test('API transport supplies tenant and CSRF but never an identity header',async()=>{const api=new ApiClient(config);api.setScope('tenant-1','csrf-token');let request;globalThis.fetch=async(url,init)=>{request={url,init};return Response.json({id:'record'})};await api.call('createWorkItem',{body:{title:'New'}},{key:'operation-123'});assert.equal(request.url,'/api/v1/work-items');assert.equal(request.init.headers.get('X-Tenant-Id'),'tenant-1');assert.equal(request.init.headers.get('X-CSRF-Token'),'csrf-token');assert.equal(request.init.headers.get('AccessKey'),null);assert.equal(request.init.headers.get('X-User-Id'),null);assert.equal(request.init.redirect,'error')})
test('generated operation routes safely encode parameters',async()=>{const api=new ApiClient(config);let url;globalThis.fetch=async u=>{url=u;return Response.json([])};await api.call('listViews',{path:{workspace:'a/b?c'}});assert.equal(url,'/api/v1/workspaces/a%2Fb%3Fc/views')})
test('API error retains safe code/request ID and conflict details',async()=>{globalThis.fetch=async()=>Response.json({error:{code:'revision_conflict',message:'Changed',request_id:'req-1',details:{current:2}}},{status:409});await assert.rejects(new ApiClient(config).request('/api/v1/work-items'),e=>e instanceof ApiError&&e.status===409&&e.requestId==='req-1')})
test('HTML API response is not treated as data',async()=>{globalThis.fetch=async()=>new Response('<html>Login</html>',{headers:{'Content-Type':'text/html'}});await assert.rejects(new ApiClient(config).request('/api/v1/work-items'),e=>e.code==='unexpected_content')})
test('transport failures produce an explicit error, not an empty dataset',async()=>{globalThis.fetch=async()=>{throw Error('network')};await assert.rejects(new ApiClient(config).request('/api/v1/work-items'),e=>e.code==='transport_error')})
test('API refuses arbitrary external endpoints',async()=>{await assert.rejects(new ApiClient(config).request('https://attacker.test'),/scoped/)} )

test('appearance mode is independent from visual personality',()=>{assert.equal(themeModel.resolveColorMode('system',true),'dark');assert.equal(themeModel.resolveColorMode('system',false),'light');assert.equal(themeModel.resolveColorMode('light',true),'light');assert.equal(themeModel.isColorModePreference('operations'),false)})
test('surface presentation converts dense side surfaces to mobile sheets',()=>{assert.equal(surface.resolveSurfaceKind('inspector',{width:480,height:900}),'sheet');assert.equal(surface.resolveSurfaceKind('inspector',{width:1400,height:900}),'inspector');assert.equal(surface.normalizeSurfaceCapabilities('dossier').dockable,true)})
test('command registry exposes one action consistently by permission selection and mode',()=>{const defs=[{id:'archive',label:'Archive',entity:'work_items',permission:'write',requiresSelection:true,modes:['browse','bulk'],placements:['toolbar','selection','palette']}];const ctx={entity:'work_items',permissions:['read','write'],selectionCount:2,mode:'bulk'};assert.equal(commands.resolveCommands(defs,ctx,'selection')[0].id,'archive');assert.equal(commands.resolveCommands(defs,{...ctx,selectionCount:0},'selection').length,0);assert.equal(commands.resolveCommands(defs,{...ctx,permissions:['read']},'palette').length,0)})
test('adaptive layout preserves complexity while changing presentation',()=>{assert.equal(layouts.resolveLayout({width:1900,hasSelection:true}).inspector,'docked');assert.equal(layouts.resolveLayout({width:700,hasSelection:true}).inspector,'drawer');assert.equal(layouts.resolveLayout({width:500,hasSelection:true}).inspector,'sheet');assert.equal(layouts.resolveLayout({width:1900,hasSelection:true,focusMode:true}).inspector,'hidden')})

test('surface stack enforces top-most layering and closes descendants with parents',()=>{let current=[];current=surfaceStack.openSurface(current,{id:'dossier',kind:'dossier'});current=surfaceStack.openSurface(current,{id:'confirm',kind:'modal'});assert.equal(surfaceStack.topSurface(current).id,'confirm');assert.equal(surfaceStack.surfaceLayer(current,'confirm')>surfaceStack.surfaceLayer(current,'dossier'),true);assert.deepEqual(surfaceStack.closeSurface(current,'dossier'),[])})

test('typed field draft helpers reject ambiguity and normalize values',()=>{assert.equal(fieldDraft.parseIntegerDraft('42','Count'),42);assert.throws(()=>fieldDraft.parseIntegerDraft('4.2','Count'));assert.equal(fieldDraft.parseNumberDraft('4.2','Value'),4.2);assert.equal(fieldDraft.parseBooleanDraft('false'),false);assert.match(fieldDraft.datetimeInputToIso('2026-09-07T14:30','When'),/Z$/)})
test('rich field draft helpers validate structured data and choices',()=>{assert.deepEqual(fieldDraft.parseJsonObjectDraft('{\"owner\":\"ops\"}','Metadata'),{owner:'ops'});assert.throws(()=>fieldDraft.parseJsonObjectDraft('[1,2]','Metadata'));assert.throws(()=>fieldDraft.parseJsonObjectDraft('{broken','Metadata'));assert.deepEqual(fieldDraft.parseMultiSelectDraft('[\"a\",\"b\"]','Tags',['a','b','c'],true),['a','b']);assert.throws(()=>fieldDraft.parseMultiSelectDraft('[]','Tags',['a'],true));assert.throws(()=>fieldDraft.parseMultiSelectDraft('[\"x\"]','Tags',['a'],false));assert.match(fieldDraft.readJsonDraft({x:1}),/\"x\"/);assert.equal(fieldDraft.readMultiSelectDraft(['a']),'[\"a\"]')})


test('generic workspace field parser enforces read-only and numeric bounds',()=>{const numberField={key:'pct',label:'Percent',kind:'percent',required:true,nullable:false,max_length:null,choices:[],minimum:0,maximum:100,step:1,unit:'%',read_only:false};assert.equal(fieldDraft.parseWorkspaceFieldDraft(numberField,'42'),42);assert.throws(()=>fieldDraft.parseWorkspaceFieldDraft(numberField,'120'));assert.throws(()=>fieldDraft.parseWorkspaceFieldDraft({...numberField,read_only:true},'1'))})

test('workspace state sanitizes stale view data and preserves supported projection intent',()=>{const definition={key:'work_items',label:'Work items',description:'',schema_version:1,fields:[{key:'status',label:'Status',kind:'select',required:true,nullable:false,max_length:null,choices:['open','done'],minimum:null,maximum:null,step:null}],columns:['title','status'],capabilities:['board'],primary_field:'title',filter_keys:['status'],sort_keys:['updated_at'],visualizations:['table','board']};const available=workspaceState.resolveWorkspaceVisualizations(definition,['table','board','graph']);assert.deepEqual(available,['table','board']);const view=workspaceState.sanitizeWorkspaceView(definition,available,{search:'abc',filters:{status:'open',invented:'x'},group_by:'status',sort:'invented',visualization:'board',columns:[{colId:'status',width:180},{colId:'invented',width:200}]},'compact');assert.equal(view.visualization,'board');assert.deepEqual(view.filters,{status:'open'});assert.equal(view.group_by,'status');assert.equal(view.sort,'updated_at');assert.equal(view.columns.length,1);assert.equal(view.density,'compact')})
test('workspace state rejects stale visualization by falling back deterministically',()=>{const definition={key:'x',label:'X',description:'',schema_version:1,fields:[],columns:[],capabilities:[],primary_field:'title',filter_keys:[],sort_keys:['updated_at'],visualizations:['table','board']};assert.equal(workspaceState.sanitizeWorkspaceView(definition,['table','board'],{visualization:'graph'}).visualization,'table')})


test('operational table model groups rows and preserves at least the identity column',async()=>{
 const model=await import(pathToFileURL(join(root,'platform/workspace/tableModel.js')).href)
 const rows=[{id:'2',revision:1,archived:false,status:'open',title:'B'},{id:'1',revision:1,archived:false,status:'done',title:'A'},{id:'3',revision:1,archived:false,status:'open',title:'C'}]
 assert.deepEqual(model.groupRows(rows,'status').map(group=>[group.label,group.rows.map(row=>row.id)]),[['done',['1']],['open',['2','3']]])
 const definition={key:'x',label:'X',description:'',schema_version:1,fields:[{key:'title',label:'Title',kind:'text',required:true,nullable:false,max_length:100,choices:[],minimum:null,maximum:null,step:null},{key:'status',label:'Status',kind:'select',required:true,nullable:false,max_length:null,choices:['open','done'],minimum:null,maximum:null,step:null}],columns:['title','status'],capabilities:[],primary_field:'title',filter_keys:['status'],sort_keys:['title'],visualizations:['table']}
 let columns=model.setColumnVisible(definition,[],'status',false)
 assert.deepEqual(model.visibleColumnIds(definition,columns),['title'])
 columns=model.setColumnVisible(definition,columns,'title',false)
 assert.deepEqual(model.visibleColumnIds(definition,columns),['title'])
 assert.equal(model.materializeColumns(definition,[])[0].width,320)
})

test('planning critical path follows longest dependency chain and date shift is deterministic',async()=>{
 const {criticalPath,shiftIsoDate}=await import(pathToFileURL(join(root,'platform/workspace/planningModel.js')).href)
 const path=criticalPath([{id:'a',duration:2},{id:'b',duration:5},{id:'c',duration:3},{id:'d',duration:2}],[{source:'b',target:'a'},{source:'c',target:'b'},{source:'d',target:'a'}])
 assert.deepEqual(path,['a','b','c']);assert.equal(shiftIsoDate('2026-09-07',2),'2026-09-09')
})

test('rack connection trace finds deterministic shortest multi-hop path',async()=>{
 const {traceRackConnections}=await import(pathToFileURL(join(root,'platform/workspace/rackModel.js')).href)
 const path=traceRackConnections([{id:'ab',source:'a',target:'b'},{id:'bc',source:'b',target:'c'},{id:'ad',source:'a',target:'d'}],'a','c')
 assert.deepEqual(path,{nodes:['a','b','c'],edges:['ab','bc']});assert.deepEqual(traceRackConnections([], 'a','z'),{nodes:[],edges:[]})
})

test('SPC model matches deterministic engineering fixtures',async()=>{
  const module=await import(pathToFileURL(join(root,'platform/engineering/spcModel.js')).href)
  const chart=module.imr([10,11,10,12,11,10,9,10])
  assert.equal(chart.center,10.375)
  assert.deepEqual(chart.movingRanges,[1,1,2,1,1,1,1])
  const cap=module.capability([99.7,100.2,100.1,99.9,100,100.3,99.8,100.1,100,99.9],99,101)
  assert.ok(cap.cp>1&&cap.cpk>1&&cap.pp>1&&cap.ppk>1)
  const xbar=module.xbarR([[10,11,9,10],[10,10,11,9],[12,11,10,11],[9,10,9,10]])
  assert.equal(xbar.subgroupSize,4)
  assert.equal(xbar.means.length,4)
  assert.deepEqual(module.ewma([10,12,14],.5),[10,11,12.5])
  assert.deepEqual(module.pareto(['A','B','A','C','A','B']).map(row=>row.category),['A','B','C'])
  const flags=module.runRuleFlags([1,2,3,4,5,6,7,8,9,10],0)
  assert.ok(flags.eightOnOneSide.includes(7)&&flags.sixPointTrend.includes(5))
})

test('semiconductor model sanitizes wafer cells, diffs recipes and summarizes state utilization',async()=>{
 const model=await import(pathToFileURL(join(root,'packs/semiconductor/model.js')).href)
 const raw={good_bins:['1'],cells:[{x:0,y:0,bin:'1',value:2.1},{x:1,y:0,bin:'2',defect:'scratch'},{x:1,y:0,bin:'3'},{x:9,y:9,bin:'4'}]}
 assert.deepEqual(model.waferCells(raw,2,2).map(cell=>cell.bin),['1','2'])
 assert.equal(model.waferGoodBins(raw).has('1'),true)
 assert.deepEqual(model.recipeDiff({a:1,b:2},{a:1,b:3,c:4}),[{key:'b',before:2,after:3},{key:'c',before:undefined,after:4}])
 const use=model.utilization([{state:'production',duration:60},{state:'standby',duration:30},{state:'production',duration:30}])
 assert.equal(use[0].state,'production');assert.equal(use[0].percent,75)
})

test('software engineering pack models parse pipeline, incident and trace data safely',async()=>{
 const model=await import(pathToFileURL(join(root,'packs/software-engineering/model.js')).href)
 assert.deepEqual(model.pipelineStages({items:[{id:'build',name:'Build',status:'passed',duration_seconds:12}]}),[{id:'build',name:'Build',status:'passed',durationSeconds:12,message:''}])
 assert.deepEqual(model.incidentEvents({events:[{at:'2026-09-07T12:02Z',message:'B'},{at:'2026-09-07T12:01Z',message:'A'}]}).map(e=>e.message),['A','B'])
 const waterfall=model.traceWaterfall([{span_id:'a',timestamp:'2026-09-07T12:00:00Z',duration_ms:100,operation:'root'},{span_id:'b',parent_span_id:'a',timestamp:'2026-09-07T12:00:00.020Z',duration_ms:40,operation:'db'}])
 assert.equal(waterfall.spans.length,2);assert.equal(waterfall.spans[0].offsetPercent,0);assert.ok(waterfall.spans[1].offsetPercent>0)
 assert.deepEqual(model.objectDiff({a:1},{a:2,b:3}),[{key:'a',before:1,after:2},{key:'b',before:undefined,after:3}])
})
