import {createHash} from 'node:crypto'
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs'
import {resolve} from 'node:path'
import {expect,test,type Page} from '@playwright/test'

type Destination={workspace:string;label:string;group:string}
const root=resolve(process.cwd(),'..')
const app=JSON.parse(readFileSync(resolve(root,'backend/app/config/application.json'),'utf8')) as {navigation:Destination[]}
const destinations=app.navigation
const evidenceRoot=resolve(root,'evidence/current/uiqa/rendered/chg185/populated')
const sourceIdentity={candidate_sha:process.env.UIQA_CHECKOUT_COMMIT??null,candidate_tree:process.env.UIQA_CANDIDATE_TREE??null,candidate_version:process.env.UIQA_CANDIDATE_VERSION??null,executable_source_commit:process.env.UIQA_EXECUTABLE_SOURCE_COMMIT??process.env.UIQA_SOURCE_COMMIT??null,source_digest:process.env.UIQA_SOURCE_DIGEST??null}
const expectedSamples:Record<string,string>={
 work_items:'Qualify synthetic process excursion evidence',projects:'Process capability recovery',racks:'FAB-A · Bay 04 · Rack R12',equipment:'CAP-7 chamber controller',
 knowledge_entries:'Runbook · chamber drift triage',investigations:'Uniformity drift after PM-204',research:'Can pressure compensation recover',risks:'Unreviewed pressure correction',plan_tasks:'Chamber capability recovery',
 diagram_documents:'Chamber 5N process and telemetry flow',process_measurements:'Within-wafer uniformity',wafer_runs:'WFR-SYN-204-03',manufacturing_lots:'LOT-SYN-204',equipment_states:'CAP-7 deposition chamber',
 process_recipes:'Uniformity recovery',software_services:'wafer-telemetry-api',delivery_runs:'deploy-syn-2041',observability_events:'P95 sample latency crossed the local warning threshold.',incidents:'INC-SYN-204',service_objectives:'Telemetry ingest availability',system:'System workspace',
}

async function capture(page:Page,name:string){
 const path=resolve(evidenceRoot,name);mkdirSync(resolve(path,'..'),{recursive:true});await page.screenshot({path,animations:'disabled'});return path.replace(`${root}/`,'')
}

async function measureTaskEconomy(page:Page){
 return page.evaluate(()=>{
  const task=document.querySelector<HTMLElement>('[data-testid="workspace-task-start"]')
  const action=document.querySelector<HTMLElement>('[data-testid="workspace-primary-actions"] button')
  const primary=document.querySelector<HTMLElement>('.workspace-primary')
  const material=primary?.firstElementChild instanceof HTMLElement?primary.firstElementChild:null
  const taskBounds=task?.getBoundingClientRect(),actionBounds=action?.getBoundingClientRect(),materialBounds=material?.getBoundingClientRect()
  const materialVisiblePx=materialBounds?Math.max(0,Math.min(materialBounds.bottom,innerHeight)-Math.max(materialBounds.top,0)):0
  return {viewport:{width:innerWidth,height:innerHeight},task_start_top:taskBounds?.top??null,task_start_bottom:taskBounds?.bottom??null,action_top:actionBounds?.top??null,action_bottom:actionBounds?.bottom??null,task_start_visible:Boolean(taskBounds&&taskBounds.top>=0&&taskBounds.top<innerHeight),action_reachable:Boolean(actionBounds&&actionBounds.top>=0&&actionBounds.bottom<=innerHeight),material_selector:material?`.workspace-primary > ${material.tagName.toLowerCase()}${material.className&&typeof material.className==='string'?`.${material.className.trim().replace(/\s+/g,'.')}`:''}`:null,material_top:materialBounds?.top??null,material_bottom:materialBounds?.bottom??null,material_visible_px:Math.round(materialVisiblePx),document_scroll_width:document.documentElement.scrollWidth,body_scroll_width:document.body.scrollWidth}
 })
}

async function measureIntersection(page:Page,locator:ReturnType<Page['locator']>){
 return locator.evaluate(element=>{const bounds=element.getBoundingClientRect();return Math.max(0,Math.min(bounds.bottom,innerHeight)-Math.max(bounds.top,0))})
}

test('CHG-185 populated routed product visual qualification',async({page})=>{
 test.setTimeout(300000)
 expect(destinations).toHaveLength(21)
 const screenshots:Array<{workspace:string;label:string;group:string;viewport:string;path:string;sample_visible:boolean;sample_visible_px:number;material_visible_px:number;material_selector:string|null;heading:string|null}> = []
 for(const viewport of [{width:1440,height:900,label:'desktop-1440x900'},{width:390,height:844,label:'mobile-390x844'}] as const){
  await page.setViewportSize({width:viewport.width,height:viewport.height})
  for(const destination of destinations){
   const workspace=destination.workspace,path=`/${workspace.replaceAll('_','-')}`
   await page.goto(path);const task=page.locator('[data-testid="workspace-task-start"]');await expect(task).toBeVisible({timeout:15000})
   const sample=expectedSamples[workspace]!;const sampleLocator=workspace==='system'?page.getByRole('heading',{name:'System workspace',exact:true}):page.getByText(sample,{exact:false}).first()
   await expect(sampleLocator).toBeVisible({timeout:15000})
   const material=page.locator('.workspace-primary > :first-child').first()
   await expect(material).toBeVisible({timeout:15000})
   const taskEconomy=await measureTaskEconomy(page),sampleVisiblePx=await measureIntersection(page,material)
   expect(sampleVisiblePx,`${workspace} representative content must intersect the initial ${viewport.label} viewport`).toBeGreaterThan(0)
   if(viewport.label==='mobile-390x844')expect(taskEconomy.material_visible_px,`${workspace} populated material content needs at least 64 visible CSS pixels`).toBeGreaterThanOrEqual(64)
   if(['equipment_states','incidents','process_measurements','service_objectives'].includes(workspace)){
    const expectedLabel={equipment_states:'State timeline',incidents:'Incident command',process_measurements:'SPC',service_objectives:'SLO'}[workspace]!
    await expect(page.locator('.workspace-summary').getByText(expectedLabel,{exact:true})).toBeVisible()
   }
   expect(await page.locator('body').innerText()).not.toMatch(/state_timeline|State_timeline|incident_command|Incident_command/)
   const output=await capture(page,`${workspace}/${viewport.label}.png`)
   screenshots.push({workspace,label:destination.label,group:destination.group,viewport:viewport.label,path:output,sample_visible:true,sample_visible_px:sampleVisiblePx,material_visible_px:taskEconomy.material_visible_px,material_selector:taskEconomy.material_selector,heading:await task.locator('h1').first().textContent()})
  }
 }
 const manifest={schema_version:1,request:'CHG-185',...sourceIdentity,fixture:'local_synthetic_demo',fixture_production_evidence:false,viewport_dpr:1,surface_count:destinations.length,viewport_count:2,screenshot_count:screenshots.length,screenshots,matrix_source_sha256:createHash('sha256').update(readFileSync(resolve(process.cwd(),'tests/e2e/ui-state-matrix.json'))).digest('hex')}
 writeFileSync(resolve(evidenceRoot,'manifest.json'),`${JSON.stringify(manifest,null,2)}\n`)
 expect(screenshots).toHaveLength(42)
})

test('CHG-185 rack, planning, diagram, SPC and system data states',async({page})=>{
 test.setTimeout(120000)
 await page.setViewportSize({width:1440,height:900})
 await page.goto('/racks');await page.getByRole('button',{name:'Rack',exact:true}).click();const devices=page.locator('.rack-device');await expect(devices).toHaveCount(4);await page.getByRole('button',{name:/CAP-7 chamber controller/}).click()
 await expect(page.locator('.rack-inspector')).toContainText('CAP-7 chamber controller');await expect(page.locator('.rack-inspector')).toContainText('CAB-SYN-1001')
 await expect(page.locator('.rack-device.selected')).toHaveCount(1);await expect(page.locator('.rack-device.selected')).toBeVisible()
 const rackGeometry=await devices.evaluateAll(elements=>elements.map(element=>{const bounds=element.getBoundingClientRect();return {label:element.textContent?.trim()??'',top:bounds.top,bottom:bounds.bottom,left:bounds.left,right:bounds.right,visible:bounds.bottom>0&&bounds.top<innerHeight&&bounds.right>0&&bounds.left<innerWidth}}))
 expect(rackGeometry.filter(device=>device.visible).length).toBeGreaterThanOrEqual(3)
 const rackEstateShot=await capture(page,'rack-occupied-estate-selected-1440x900.png')
 const traceSearch=page.locator('.rack-trace-tools input');await traceSearch.fill('NW-24 dual-fabric leaf switch');await page.getByRole('button',{name:'Trace to NW-24 dual-fabric leaf switch'}).click();await expect(page.locator('.rack-trace-banner.active')).toBeVisible()
 const rackTraceShot=await capture(page,'rack-selected-connected-trace-1440x900.png')
 await page.goto('/plan-tasks');await expect(page.locator('.planning-workbench')).toContainText('Repeat upper-limit metrology subgroup');const planningShot=await capture(page,'planning-populated-1440x900.png')
 await page.goto('/diagram-documents');await expect(page.locator('.diagram-node')).toHaveCount(4);await page.locator('.diagram-node').first().click();await expect(page.locator('.diagram-inspector')).toContainText('Selection inspector');const diagramShot=await capture(page,'diagram-selected-inspector-1440x900.png')
 await page.goto('/process-measurements');await expect(page.locator('.spc-workbench')).toBeVisible();await expect(page.locator('.spc-workbench')).toContainText('Within-wafer uniformity');const spcShot=await capture(page,'spc-exception-series-1440x900.png')
 await page.goto('/system');const systemShots:string[]=[]
 for(const section of ['Members','Events','Notifications']){await page.getByRole('tab',{name:section,exact:true}).click();const system=page.locator('.workspace-primary');if(section==='Members'){await expect(system).toContainText('Members & roles');await expect(system).toContainText('demo.viewer')}if(section==='Events'){await expect(system).toContainText('Durable event stream');await expect(page.getByRole('region',{name:'Durable events'}).locator('article').first()).toBeVisible()}if(section==='Notifications'){await expect(system).toContainText('Review SPC upper-limit samples');}systemShots.push(await capture(page,`system-${section.toLowerCase()}-1440x900.png`))}
 const manifest={schema_version:2,request:'CHG-185',...sourceIdentity,fixture:'local_synthetic_demo',rack:{geometry_proof:{devices:4,visible_device_count:rackGeometry.filter(device=>device.visible).length,selected_device:'CAP-7 chamber controller',path:rackEstateShot},interaction_proof:{selected:true,connected:true,trace:true,path:rackTraceShot}},planning:planningShot,diagram:diagramShot,spc:spcShot,system:{local_members:true,events:true,notifications:true,screenshots:systemShots}}
 writeFileSync(resolve(evidenceRoot,'selected-states.json'),`${JSON.stringify(manifest,null,2)}\n`)
})

test('CHG-185 mobile task economy budget and fault sensitivity',async({page})=>{
 test.setTimeout(90000)
 const budgets=[]
 for(const viewport of [{width:390,height:844},{width:320,height:800}] as const){
  await page.setViewportSize(viewport);await page.goto('/work-items');await expect(page.getByText('Qualify synthetic process excursion evidence',{exact:false}).first()).toBeVisible()
  const measured=await measureTaskEconomy(page)
  expect(measured.task_start_top).not.toBeNull();expect(measured.task_start_top!).toBeLessThanOrEqual(180)
  expect(measured.action_reachable).toBe(true);expect(measured.action_bottom!).toBeLessThanOrEqual(300)
  if(viewport.width===390)expect(measured.material_visible_px).toBeGreaterThanOrEqual(64)
  expect(measured.document_scroll_width).toBeLessThanOrEqual(viewport.width+1);expect(measured.body_scroll_width).toBeLessThanOrEqual(viewport.width+1)
  budgets.push(measured);await capture(page,`work-items-task-budget-${viewport.width}x${viewport.height}.png`)
 }
 await page.setViewportSize({width:390,height:844});await page.goto('/work-items');await expect(page.getByText('Qualify synthetic process excursion evidence',{exact:false}).first()).toBeVisible()
 const baseline=await measureTaskEconomy(page);expect(baseline.material_visible_px).toBeGreaterThanOrEqual(64)
 await page.addStyleTag({content:'.workspace-summary{min-height:420px!important}'})
 const faulted=await measureTaskEconomy(page),faultRejected=faulted.material_visible_px<64
 expect(faultRejected,'expanded workspace summary chrome must fail the material-content intersection budget').toBe(true)
 writeFileSync(resolve(evidenceRoot,'mobile-task-economy.json'),`${JSON.stringify({schema_version:2,request:'CHG-185',...sourceIdentity,limits:{task_start_top_max_px:180,primary_action_bottom_max_px:300,material_content_visible_px_min:64},budgets,faulted_workspace_chrome:{mutation:'workspace summary min-height 420px',measurement:faulted,violated_budget:'material_content_visible_px >= 64',oracle_rejected:faultRejected}},null,2)}\n`)
})

test('CHG-185 mobile workspace controls keep scope visible and applied state discoverable',async({page})=>{
 test.setTimeout(90000);await page.setViewportSize({width:390,height:844});await page.goto('/work-items')
 const controls=page.locator('.responsive-workspace-controls'),options=controls.locator('.workspace-controls-disclosure'),summary=options.locator('summary')
 await expect(controls.getByRole('textbox',{name:'Search records'})).toBeVisible();await expect(controls.getByRole('button',{name:'Active',exact:true})).toHaveAttribute('aria-pressed','true')
 await expect(options).not.toHaveAttribute('open','')
 await summary.click();await expect(options).toHaveAttribute('open','')
 await expect(options.getByRole('combobox',{name:'Sort all results'})).toBeVisible();await expect(options.getByRole('heading',{name:'Density'})).toBeVisible();await expect(options.getByRole('heading',{name:'Columns'})).toBeVisible();await expect(options.locator('.workspace-view-tools')).toBeVisible()
 const filter=options.locator('select[aria-label^="Filter by "]').first();await expect(filter).toBeVisible();const optionValue=await filter.locator('option').nth(1).getAttribute('value'),optionLabel=await filter.locator('option:checked').textContent()
 expect(optionValue).toBeTruthy();await filter.selectOption(optionValue!)
 const appliedLabel=await filter.locator('option:checked').textContent();await summary.click();await expect(options).not.toHaveAttribute('open','');await expect(summary).toContainText(appliedLabel!.trim())
 const retainedValue=await filter.inputValue()
 const evidence={schema_version:1,request:'CHG-185',...sourceIdentity,viewport:{width:390,height:844},search_visible:true,dataset_scope:'Active',disclosure_count:1,sort_display_saved_view_reachable:true,filter_value:optionValue,filter_label:appliedLabel?.trim(),closed_summary:await summary.innerText(),state_retained:retainedValue===optionValue}
 expect(evidence.state_retained).toBe(true);const path=await capture(page,'work-items-mobile-controls-applied-state-390x844.png');writeFileSync(resolve(evidenceRoot,'mobile-controls.json'),`${JSON.stringify({...evidence,screenshot:path},null,2)}\n`)
})

test('CHG-185 desktop active navigation reveals deep destinations without needless scrolling',async({page})=>{
 test.setTimeout(90000);await page.setViewportSize({width:1440,height:900});await page.goto('/work-items')
 const nav=page.locator('.sidebar nav')
 const inspect=async(path:string)=>page.locator(`.sidebar nav a[href="${path}"]`).evaluate(element=>{const nav=element.closest('nav')!,item=element.getBoundingClientRect(),scrollport=nav.getBoundingClientRect();return {label:element.textContent?.trim(),top:item.top,bottom:item.bottom,nav_top:scrollport.top,nav_bottom:scrollport.bottom,scroll_top:nav.scrollTop,scroll_height:nav.scrollHeight,client_height:nav.clientHeight,inside:item.top>=scrollport.top&&item.bottom<=scrollport.bottom}})
 const serviceLink=nav.locator('a[href="/incidents"]');await nav.evaluate(element=>{element.scrollTop=0});const serviceBefore=await inspect('/incidents');expect(serviceBefore.inside).toBe(false)
 await page.goto('/incidents');await expect(page.getByRole('heading',{name:'Incident command',exact:true})).toBeVisible();await expect.poll(async()=>{const state=await inspect('/incidents');return state.inside?'inside':JSON.stringify(state)},{message:'Service operations active navigation link must be fully inside the sidebar scrollport after route stabilization'}).toBe('inside');const serviceAfter=await inspect('/incidents');expect(serviceAfter.inside).toBe(true);expect(await serviceLink.getAttribute('aria-current')).toBe('page');const serviceShot=await capture(page,'desktop-nav-service-operations-1440x900.png')
 await nav.evaluate(element=>{element.scrollTop=0});const systemBefore=await inspect('/system');expect(systemBefore.inside).toBe(false)
 await page.goto('/system');await expect(page.getByRole('heading',{name:'System workspace',exact:true})).toBeVisible();await expect.poll(async()=>{const state=await inspect('/system');return state.inside?'inside':JSON.stringify(state)},{message:'System active navigation link must be fully inside the sidebar scrollport after route stabilization'}).toBe('inside');const systemAfter=await inspect('/system');expect(systemAfter.inside).toBe(true);expect(await nav.locator('a[href="/system"]').getAttribute('aria-current')).toBe('page');const focusStolen=await nav.evaluate(element=>element.contains(document.activeElement));expect(focusStolen).toBe(false);const systemShot=await capture(page,'desktop-nav-system-1440x900.png')
 await nav.evaluate(element=>{element.scrollTop=0});await page.goto('/projects');await expect(page.getByRole('heading',{name:'Projects',exact:true})).toBeVisible();const visibleScrollTop=await nav.evaluate(element=>element.scrollTop);expect(visibleScrollTop).toBe(0)
 writeFileSync(resolve(evidenceRoot,'desktop-active-nav.json'),`${JSON.stringify({schema_version:1,request:'CHG-185',...sourceIdentity,viewport:{width:1440,height:900},scroll_owner:'.sidebar nav',service_operations:{before:serviceBefore,after:serviceAfter,screenshot:serviceShot},system:{before:systemBefore,after:systemAfter,screenshot:systemShot},already_visible:{destination:'Projects',scroll_top_after_route:visibleScrollTop,no_unnecessary_scroll:true},focus_stolen:focusStolen},null,2)}\n`)
})

test('CHG-185 true empty, no-match, request-error and permission states',async({page})=>{
 test.setTimeout(90000);await page.setViewportSize({width:1440,height:900})
 const payload={items:[],total:0,limit:50,offset:0}
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(payload)}));await page.goto('/work-items')
 await expect(page.getByRole('heading',{name:'No active work items yet',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:/No matching work items/})).toHaveCount(0);const emptyShot=await capture(page,'states/empty-active-1440x900.png')
 await page.getByRole('button',{name:'Archived',exact:true}).click();await expect(page.getByRole('heading',{name:'No archived work items',exact:true})).toBeVisible();const archivedShot=await capture(page,'states/empty-archived-1440x900.png')
 await page.getByRole('button',{name:'Active',exact:true}).click()
 await page.getByRole('textbox',{name:'Search records'}).fill('zz-no-match-synthetic-185');await expect(page.getByRole('heading',{name:'No matching work items',exact:true})).toBeVisible();const noMatchShot=await capture(page,'states/no-match-1440x900.png')
 await page.unroute('**/api/v1/work-items*');await page.route('**/api/v1/work-items*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'chg185_fixture_error',message:'Qualification fixture request failure',request_id:'chg185-error',details:null}})}));await page.goto('/work-items');const requestError=page.getByRole('alert').filter({hasText:'Qualification fixture request failure'});await expect(requestError).toBeVisible();await expect(page.getByRole('heading',{name:/No active work items/})).toHaveCount(0);const errorShot=await capture(page,'states/request-error-1440x900.png')
 await page.unroute('**/api/v1/work-items*');await page.unroute('**/api/v1/bootstrap');await page.route('**/api/v1/bootstrap',async route=>{const response=await route.fetch();const body=await response.json();body.tenants=body.tenants.map((tenant:{permissions:string[]})=>({...tenant,permissions:[]}));await route.fulfill({response,json:body})});await page.goto('/work-items')
 const readOnlyRecord=page.getByRole('button',{name:'Qualify synthetic process excursion evidence',exact:true});await expect(readOnlyRecord).toBeVisible({timeout:15000});await expect(page.getByText('Loading records…')).toHaveCount(0)
 const accessMetric=page.locator('.workspace-summary');await expect(accessMetric).toContainText('Access');await expect(accessMetric).toContainText('Read only')
 await expect(page.getByRole('button',{name:/New |Create/})).toHaveCount(0);await expect(page.getByRole('button',{name:/Edit/})).toHaveCount(0)
 const permissionShot=await capture(page,'states/read-only-1440x900.png')
 const result={schema_version:2,request:'CHG-185',...sourceIdentity,empty:{title:'No active work items yet',path:emptyShot},archived_empty:{title:'No archived work items',path:archivedShot},no_match:{title:'No matching work items',path:noMatchShot},request_error:{alert:'Qualification fixture request failure',path:errorShot},read_only:{permission:'read-only bootstrap permissions',access:'Read only',settled_populated:true,representative_record:'Qualify synthetic process excursion evidence',write_or_create_controls_absent:true,path:permissionShot}}
 writeFileSync(resolve(evidenceRoot,'truthful-states.json'),`${JSON.stringify(result,null,2)}\n`)
})

test('CHG-185 responsive stress preserves task access and section reachability',async({page})=>{
 test.setTimeout(90000);const observations:Array<Record<string,unknown>>=[]
 for(const viewport of [{width:320,height:800},{width:390,height:420}]){
  await page.setViewportSize(viewport);await page.goto('/system');await expect(page.getByRole('heading',{name:'System workspace',exact:true})).toBeVisible()
  const tabs=page.getByRole('tablist',{name:'System sections'}),last=tabs.getByRole('tab').last();await last.focus();await expect(last).toBeFocused();const revealed=await last.evaluate(element=>{const b=element.getBoundingClientRect(),o=element.closest<HTMLElement>('[role="tablist"]')!.getBoundingClientRect();return b.left>=o.left&&b.right<=o.right})
  expect(revealed).toBe(true);observations.push({viewport,final_section:await last.textContent(),focus_revealed:revealed,scroll_owner_width:await tabs.evaluate(element=>({clientWidth:element.clientWidth,scrollWidth:element.scrollWidth}))})
 }
 await page.setViewportSize({width:320,height:800});await page.goto('/work-items');await page.evaluate(()=>{document.documentElement.style.fontSize='125%';document.documentElement.style.letterSpacing='.08em';document.documentElement.style.wordSpacing='.12em';document.documentElement.dir='rtl';document.documentElement.style.scrollBehavior='auto'})
 await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible();const stress=await measureTaskEconomy(page);expect(stress.document_scroll_width).toBeLessThanOrEqual(321);expect(stress.body_scroll_width).toBeLessThanOrEqual(321)
 await page.emulateMedia({reducedMotion:'reduce',forcedColors:'active'});const media=await page.evaluate(()=>({reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches,forcedColors:matchMedia('(forced-colors: active)').matches}));expect(media).toEqual({reducedMotion:true,forcedColors:true})
 writeFileSync(resolve(evidenceRoot,'responsive-stress.json'),`${JSON.stringify({schema_version:1,request:'CHG-185',...sourceIdentity,system_sections:observations,large_text_rtl:stress,media,scope:'Chromium only; no physical device, screen-reader, IME or non-Chromium claim'},null,2)}\n`)
})

test('CHG-185 narrow dossier section selector reaches all ten sections',async({page})=>{
 test.setTimeout(90000);await page.setViewportSize({width:390,height:844});await page.goto('/work-items')
 const record=page.getByRole('button',{name:'Qualify synthetic process excursion evidence',exact:true});await expect(record).toBeVisible();await record.click()
 const dialog=page.getByRole('dialog',{name:'Qualify synthetic process excursion evidence'});await expect(dialog).toBeVisible();const selector=dialog.getByRole('combobox',{name:'Record section'}),sections=['overview','fields','relationships','activity','history','compare','comments','files','audit','actions']
 await expect(selector.locator('option')).toHaveCount(10);const screenshots=[]
 for(const section of sections){await selector.selectOption(section);await expect(selector).toHaveValue(section);expect(await dialog.locator('.surface-body').isVisible()).toBe(true);if(section==='overview')screenshots.push(await capture(page,'dossier-mobile-overview-390x844.png'));if(section==='actions'){await expect(dialog).toContainText('No additional record-specific actions are available.');expect((await dialog.innerText()).toLocaleLowerCase()).not.toContain('adapter');screenshots.push(await capture(page,'dossier-mobile-actions-390x844.png'))}}
 await selector.focus();await expect(selector).toBeFocused();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');await expect(selector).toBeFocused()
 writeFileSync(resolve(evidenceRoot,'dossier-sections.json'),`${JSON.stringify({schema_version:1,request:'CHG-185',...sourceIdentity,viewport:{width:390,height:844},section_count:sections.length,sections,keyboard_focus_reachable:true,native_select_options_present:true,headless_chromium_native_popup_selection:'UNPROVEN',screenshots},null,2)}\n`)
})

test('CHG-185 revision conflict preserves the edited draft for recovery',async({page})=>{
 test.setTimeout(90000);await page.setViewportSize({width:1440,height:900});await page.goto('/work-items')
 await page.getByRole('button',{name:'Qualify synthetic process excursion evidence',exact:true}).click();const dossier=page.getByRole('dialog',{name:'Qualify synthetic process excursion evidence'});await dossier.getByRole('menuitem',{name:'Edit'}).click()
 const form=page.getByRole('dialog',{name:'Edit work item'}),title=form.getByRole('textbox',{name:'Title'});await title.fill('Updated synthetic process qualification title')
 await page.route('**/api/v1/work-items/*',async route=>{if(route.request().method()!=='PUT')return route.fallback();await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:{code:'revision_conflict',message:'This record changed. Review the current revision before saving again.',request_id:'chg185-conflict',details:{current:{revision:2}}}})})})
 await form.getByRole('button',{name:'Save changes'}).click();await expect(form.getByRole('alert')).toContainText('This record changed');await expect(title).toHaveValue('Updated synthetic process qualification title')
 const path=await capture(page,'states/revision-conflict-retained-draft-1440x900.png');writeFileSync(resolve(evidenceRoot,'revision-conflict.json'),`${JSON.stringify({schema_version:1,request:'CHG-185',...sourceIdentity,precondition:'revision-backed work item dossier opened',input:'changed title',visible_result:'server revision conflict',correct_object:'same work item edit form',forbidden_effect:'draft is not discarded or persisted over revision 2',recovery:'review latest revision and retry after reconciling',next_legitimate_action:'keep or close the preserved draft',draft_retained:true,screenshot:path},null,2)}\n`)
})
