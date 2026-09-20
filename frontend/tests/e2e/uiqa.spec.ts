import {createHash} from 'node:crypto'
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs'
import {basename,dirname,resolve} from 'node:path'
import {test,expect,type Locator,type Page,type TestInfo} from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import {RuntimeDimensionProof} from '../../src/platform/testing/uiqa-proof'

type MatrixRow={state_id:string;material_state_class:string;required_dimensions:string[];browser_test_id:string;required_evidence:{artifact_locators:string[];axe_serious_critical:boolean}}
const root=resolve(process.cwd(),'..')
const matrixFile=resolve(process.cwd(),'tests/e2e/ui-state-matrix.json')
const matrix=JSON.parse(readFileSync(matrixFile,'utf8')) as {matrix_id:string;required_dimensions:string[];rows:MatrixRow[]}
const rows=matrix.rows
const rowByState=new Map(rows.map(row=>[row.state_id,row]))
const proofByTestInfo=new WeakMap<TestInfo,RuntimeDimensionProof>()
const results: Array<{state_id:string;browser_test_id:string;status:'PASS'|'FAIL';exercised_dimensions:string[];artifact_locators:string[]}>=[]
const renderedRoot=resolve(process.env.UIQA_RENDERED_DIR??resolve(root,'evidence/current/uiqa/rendered'))
const resultsFile=resolve(process.env.UIQA_OUTPUT??resolve(root,'evidence/current/uiqa/ui-state-matrix-results.json'))

function rowFor(stateId:string):MatrixRow{
 const row=rowByState.get(stateId)
 if(!row)throw new Error(`Unknown UI state matrix row: ${stateId}`)
 return row
}

async function writeStateEvidence(row:MatrixRow,page:Page,payload:unknown):Promise<void>{
 mkdirSync(renderedRoot,{recursive:true})
 for(const locator of row.required_evidence.artifact_locators){
  const path=resolve(root,locator)
  mkdirSync(dirname(path),{recursive:true})
  if(path.endsWith('.png'))await page.screenshot({path,fullPage:true})
  else writeFileSync(path,`${JSON.stringify({state_id:row.state_id,material_state_class:row.material_state_class,...(payload as Record<string,unknown>)},null,2)}\n`)
 }
}

async function axeSummary(page:Page){
 const report=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
 const seriousOrCritical=report.violations.filter(violation=>violation.impact==='serious'||violation.impact==='critical')
 expect(seriousOrCritical).toEqual([])
 return {total_violations:report.violations.length,serious_or_critical:seriousOrCritical.map(violation=>violation.id).sort()}
}

function matrixTest(stateId:string,body:(args:{page:Page;proof:RuntimeDimensionProof},row:MatrixRow,info:TestInfo)=>Promise<Record<string,unknown>>):void{
 const row=rowFor(stateId)
 test(`${row.browser_test_id} ${row.state_id}`,async({page},info)=>{
  info.annotations.push({type:'ui-matrix-state',description:row.state_id})
  const proof=new RuntimeDimensionProof(row.required_dimensions,matrix.required_dimensions)
  proofByTestInfo.set(info,proof)
  const payload=await body({page,proof},row,info)
  let axe:Awaited<ReturnType<typeof axeSummary>>|undefined
  if(row.required_evidence.axe_serious_critical)await proof.prove('axe.serious-critical',async()=>{axe=await axeSummary(page)})
  proof.complete()
  await writeStateEvidence(row,page,{...payload,...(axe?{axe}: {})})
 })
}

test.afterEach(({},info)=>{
 const stateId=info.annotations.find(annotation=>annotation.type==='ui-matrix-state')?.description
 if(!stateId)return
 const row=rowFor(stateId)
 const proof=proofByTestInfo.get(info)
 results.push({state_id:stateId,browser_test_id:row.browser_test_id,status:info.status===info.expectedStatus?'PASS':'FAIL',exercised_dimensions:proof?.observedDimensions()??[],artifact_locators:[...row.required_evidence.artifact_locators].sort()})
})

test.afterAll(()=>{
 mkdirSync(dirname(resultsFile),{recursive:true})
 const ordered=[...results].sort((left,right)=>left.state_id.localeCompare(right.state_id))
 const manifest={
  schema_version:2,
  result_kind:'browser-computed-uiqa',
  proof_model:'runtime-assertion-v1',
  matrix_id:matrix.matrix_id,
  matrix_sha256:createHash('sha256').update(readFileSync(matrixFile)).digest('hex'),
  checkout_commit:process.env.UIQA_CHECKOUT_COMMIT??null,
  candidate_head:process.env.UIQA_CHECKOUT_COMMIT??null,
  executable_source_commit:process.env.UIQA_EXECUTABLE_SOURCE_COMMIT??process.env.UIQA_SOURCE_COMMIT??null,
  source_digest:process.env.UIQA_SOURCE_DIGEST??null,
  source_commit:process.env.UIQA_EXECUTABLE_SOURCE_COMMIT??process.env.UIQA_SOURCE_COMMIT??null,
  overall_status:ordered.length===rows.length&&ordered.every(row=>row.status==='PASS')?'PASS':'FAIL',
  results:ordered,
 }
 writeFileSync(resultsFile,`${JSON.stringify(manifest,null,2)}\n`)
})

const contrastRatio=async(locator:ReturnType<Page['locator']>)=>locator.evaluate(element=>{
 const rgb=(value:string)=>{const match=value.match(/rgba?\(([^)]+)\)/);if(!match)return null;const parts=match[1]!.split(',').map(Number);return parts.length<3?null:[parts[0]!,parts[1]!,parts[2]!,parts[3]??1]}
 const linear=(value:number)=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4}
 const luminance=(value:number[])=>.2126*linear(value[0]!)+.7152*linear(value[1]!)+.0722*linear(value[2]!)
 const foreground=rgb(getComputedStyle(element).color)??[0,0,0,1]
 let node:Element|null=element;let background:number[]=[255,255,255,1]
 while(node){const value=rgb(getComputedStyle(node).backgroundColor);if(value&&value[3]!>0){background=value;break}node=node.parentElement}
 const fgL=luminance(foreground),bgL=luminance(background)
 return {ratio:(Math.max(fgL,bgL)+.05)/(Math.min(fgL,bgL)+.05),foreground,background}
})

async function workItemPage(page:Page):Promise<void>{
 await page.goto('/work-items')
 await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
}

function workItemPayload(items:unknown[]=[],total=items.length){return {items,total,limit:50,offset:0}}

type Geometry={viewport_css_px:number;document_scroll_width:number;document_client_width:number;body_scroll_width:number}
async function pageGeometry(page:Page):Promise<Geometry>{
 return page.evaluate(()=>({viewport_css_px:innerWidth,document_scroll_width:document.documentElement.scrollWidth,document_client_width:document.documentElement.clientWidth,body_scroll_width:document.body.scrollWidth}))
}

async function boxFullyInside(owner:Locator,control:Locator):Promise<boolean>{
 const ownerBox=await owner.boundingBox(),controlBox=await control.boundingBox()
 if(!ownerBox||!controlBox)return false
 const inset=1
 return controlBox.x>=ownerBox.x+inset&&controlBox.x+controlBox.width<=ownerBox.x+ownerBox.width-inset&&controlBox.y>=ownerBox.y+inset&&controlBox.y+controlBox.height<=ownerBox.y+ownerBox.height-inset
}

async function focusEvidence(page:Page,owner:Locator,control:Locator){
 const ownerBox=await owner.boundingBox();if(!ownerBox)throw new Error('Focus owner has no geometry')
 const viewport=await page.evaluate(()=>({width:innerWidth,height:innerHeight}))
 const controlEvidence=await control.evaluate(element=>{
  const style=getComputedStyle(element),bounds=element.getBoundingClientRect(),outlineWidth=Number.parseFloat(style.outlineWidth)||0,outlineOffset=Math.max(0,Number.parseFloat(style.outlineOffset)||0),extent=style.outlineStyle==='none'?0:outlineWidth+outlineOffset
  return {active:document.activeElement===element,focusVisible:element.matches(':focus-visible'),outline:style.outline,outlineStyle:style.outlineStyle,outlineWidth:style.outlineWidth,outlineOffset:style.outlineOffset,bounds:{left:bounds.left,right:bounds.right,top:bounds.top,bottom:bounds.bottom},focus_bounds:{left:bounds.left-extent,right:bounds.right+extent,top:bounds.top-extent,bottom:bounds.bottom+extent}}
 })
 const focusBounds=controlEvidence.focus_bounds
 return {...controlEvidence,owner_bounds:{left:ownerBox.x,right:ownerBox.x+ownerBox.width,top:ownerBox.y,bottom:ownerBox.y+ownerBox.height},viewport_bounds:{left:0,right:viewport.width,top:0,bottom:viewport.height},fully_inside_owner:focusBounds.left>=ownerBox.x&&focusBounds.right<=ownerBox.x+ownerBox.width&&focusBounds.top>=ownerBox.y&&focusBounds.bottom<=ownerBox.y+ownerBox.height,fully_inside_viewport:focusBounds.left>=0&&focusBounds.right<=viewport.width&&focusBounds.top>=0&&focusBounds.bottom<=viewport.height}
}

async function pointerScrollToEnd(page:Page,owner:Locator,target?:Locator):Promise<void>{
 await owner.waitFor({state:'visible'});await page.waitForTimeout(100);await owner.scrollIntoViewIfNeeded();await owner.hover();await page.mouse.wheel(1200,0);if(await owner.evaluate(element=>element.scrollLeft===0&&element.scrollWidth>element.clientWidth)){await page.keyboard.down('Shift');await page.mouse.wheel(0,1200);await page.keyboard.up('Shift')}if(target)await target.scrollIntoViewIfNeeded()
}

async function negativeControl(page:Page){
 return page.evaluate(()=>{
  const labels=['Overview','Members','Teams','Feature flags','Jobs','Events','Webhooks','Audit','Notifications']
  const system=document.createElement('div');system.style.cssText='position:absolute;left:0;top:0;display:flex;white-space:nowrap;z-index:-1'
  for(const label of labels){const button=document.createElement('button');button.textContent=label;button.style.cssText='flex:0 0 auto;padding:8px 13px';system.append(button)}
  document.body.append(system);const systemResult={viewport:innerWidth,documentScrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth};system.remove()
  const visualization=document.createElement('div');visualization.style.cssText='display:flex;width:100px;overflow:hidden;border:1px solid red'
  for(const label of ['Table','Board','Dashboard','Timeline']){const button=document.createElement('button');button.textContent=label;button.style.cssText='flex:0 0 auto';visualization.append(button)}
  document.body.append(visualization);const last=visualization.lastElementChild!,ownerBounds=visualization.getBoundingClientRect(),lastBounds=last.getBoundingClientRect();const visualizationResult={ownerClientWidth:visualization.clientWidth,ownerScrollWidth:visualization.scrollWidth,lastFullyInside:lastBounds.left>=ownerBounds.left&&lastBounds.right<=ownerBounds.right};visualization.remove()
  const focusOwner=(top:number)=>{const owner=document.createElement('div');owner.style.cssText=`position:absolute;left:0;top:${top}px;width:258px;height:40px;overflow:auto;display:flex;z-index:-1;contain:layout paint`;const spacer=document.createElement('span');spacer.style.cssText='flex:0 0 250px';owner.append(spacer);const target=document.createElement('button');target.textContent='Final';target.style.cssText='flex:0 0 114px;margin-right:8px;outline:3px solid red;outline-offset:3px';owner.append(target);document.body.append(owner);return {owner,target}}
  const faulty=focusOwner(0);faulty.target.focus();faulty.owner.scrollLeft=50;const faultyOwnerBounds=faulty.owner.getBoundingClientRect(),faultyTargetBounds=faulty.target.getBoundingClientRect(),faultyFocus={left:faultyTargetBounds.left-6,right:faultyTargetBounds.right+6,top:faultyTargetBounds.top-6,bottom:faultyTargetBounds.bottom+6};const faultyResult={ownerClientWidth:faulty.owner.clientWidth,ownerScrollWidth:faulty.owner.scrollWidth,focused:document.activeElement===faulty.target,focusBounds:faultyFocus,fullyInsideOwner:faultyFocus.left>=faultyOwnerBounds.left&&faultyFocus.right<=faultyOwnerBounds.right,partlyOutsideOwner:faultyFocus.left<faultyOwnerBounds.right&&faultyFocus.right>faultyOwnerBounds.right,pageLevelOverflowGreen:document.documentElement.scrollWidth<=innerWidth&&document.body.scrollWidth<=innerWidth};faulty.owner.remove()
  const sound=focusOwner(50);sound.target.focus();sound.owner.scrollLeft=sound.owner.scrollWidth-sound.owner.clientWidth;const soundOwnerBounds=sound.owner.getBoundingClientRect(),soundTargetBounds=sound.target.getBoundingClientRect(),soundFocus={left:soundTargetBounds.left-6,right:soundTargetBounds.right+6,top:soundTargetBounds.top-6,bottom:soundTargetBounds.bottom+6};const soundResult={ownerClientWidth:sound.owner.clientWidth,ownerScrollWidth:sound.owner.scrollWidth,focused:document.activeElement===sound.target,focusBounds:soundFocus,fullyInsideOwner:soundFocus.left>=soundOwnerBounds.left&&soundFocus.right<=soundOwnerBounds.right,pageLevelOverflowGreen:document.documentElement.scrollWidth<=innerWidth&&document.body.scrollWidth<=innerWidth};sound.owner.remove()
  return {system:systemResult,visualization:visualizationResult,focusContainment:{faulty:faultyResult,sound:soundResult}}
 })
}

function projectionLocator(page:Page,mode:string):Locator{
 const selectors:Record<string,string>={table:'.golden-grid',board:'.board-scroll',timeline:'.entity-timeline',calendar:'.calendar-projection',gantt:'.gantt-projection',dashboard:'.dashboard-projection',graph:'.graph-projection-wrap',planning:'.planning-workbench',incident_command:'.incident-workbench'}
 return page.locator(selectors[mode]??`.${mode.replaceAll('_','-')}-workbench`)
}

async function expectRenderedMode(page:Page,mode:string):Promise<void>{
 const projection=projectionLocator(page,mode);if(await projection.count())await expect(projection).toBeVisible();else{const summary=page.locator('.workspace-summary').getByText(mode,{exact:true});if(await summary.count())await expect(summary).toBeVisible();else await expect(page.getByRole('heading',{name:'No matching records',exact:true})).toBeVisible()}
}

matrixTest('chg34-theme-operations-primary-action',async({page,proof},row)=>{
 await workItemPage(page)
 await page.getByLabel('Appearance',{exact:true}).selectOption('dark')
 await proof.prove('theme.dark',async()=>expect(await page.getByLabel('Appearance',{exact:true}).inputValue()).toBe('dark'))
 await page.getByLabel('Theme',{exact:true}).selectOption('operations')
 const primary=page.locator('button.primary').first();const result=await contrastRatio(primary)
 await proof.prove('browser-computed',async()=>expect(result.ratio).toBeGreaterThanOrEqual(4.5))
 return {computed_contrast:result,semantic_name:await primary.getAttribute('aria-label'),theme:await page.locator('html').getAttribute('data-theme'),artifact_hint:basename(row.required_evidence.artifact_locators[0]!)}
})

matrixTest('chg34-grid-semantic-theme-modes',async({page,proof})=>{
 await workItemPage(page)
 const grid=page.getByLabel('Work items data grid');const modes:Record<string,unknown>={}
 await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024))
 for(const appearance of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(appearance);await expect(grid).toBeVisible()
  if(appearance==='light')await proof.prove('theme.light',async()=>expect(await page.getByLabel('Appearance',{exact:true}).inputValue()).toBe('light'))
  else await proof.prove('theme.dark',async()=>expect(await page.getByLabel('Appearance',{exact:true}).inputValue()).toBe('dark'))
  modes[appearance]=await grid.evaluate(element=>{
   const root=element.querySelector('.ag-root-wrapper')!,header=element.querySelector('.ag-header')!,row=element.querySelector('.ag-row')!
   const style=(node:Element)=>{const computed=getComputedStyle(node);return {background:computed.backgroundColor,color:computed.color}}
   return {root:style(root),header:style(header),row:style(row),rows:element.querySelectorAll('.ag-row').length}
 })
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high');await proof.prove('contrast.high',async()=>expect(page.locator('html')).toHaveAttribute('data-contrast','high'))
 const high=await grid.locator('.ag-row').first().evaluate(element=>({background:getComputedStyle(element).backgroundColor,color:getComputedStyle(element).color}))
 await proof.prove('browser-computed',async()=>{
  expect((modes.dark as {root:{background:string}}).root.background).not.toBe('rgb(255, 255, 255)')
  expect((modes.light as {root:{background:string;row:{background:string}}}).root.background).toBe((modes.light as {root:{background:string;row:{background:string}}}).row.background)
  expect(high.background).toBe('rgb(0, 0, 0)');expect(high.color).toBe('rgb(255, 255, 255)')
  expect((modes.light as {row:{color:string}}).row.color).not.toBe('rgb(24, 29, 31)')
  expect((modes.light as {rows:number}).rows).toBeLessThanOrEqual(55)
 })
 return {computed_modes:modes,computed_high_contrast:high,grid_role:await grid.getAttribute('role'),grid_name:await grid.getAttribute('aria-label')}
})

matrixTest('chg34-saved-view-checkbox-selection',async({page,proof})=>{
 await workItemPage(page);await page.getByRole('button',{name:'Save view',exact:true}).click()
 const dialog=page.getByRole('dialog',{name:'Save current view'});const controls=[]
 await proof.prove('semantics.role-name-state',async()=>{
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('checkbox',{name:'Favorite'})).toBeVisible()
 })
 for(const name of ['Favorite','Default for this workspace']){
  const checkbox=dialog.getByRole('checkbox',{name})
  const geometry=await checkbox.evaluate(element=>{const label=element.closest('label')!;const style=getComputedStyle(label);const bounds=element.getBoundingClientRect();return {display:style.display,direction:style.flexDirection,width:Math.round(bounds.width),height:Math.round(bounds.height),native:element instanceof HTMLInputElement}})
  expect(geometry).toMatchObject({display:'flex',direction:'row',width:16,height:16,native:true})
  if(name==='Favorite')await proof.prove('keyboard.space',async()=>{await checkbox.focus();await expect(checkbox).toBeFocused();await page.keyboard.press('Space');await expect(checkbox).toBeChecked()})
  else {await checkbox.focus();await expect(checkbox).toBeFocused();await page.keyboard.press('Space');await expect(checkbox).toBeChecked()}
  controls.push({name,geometry,checked:await checkbox.isChecked(),role:await checkbox.getAttribute('role')})
 }
 return {controls,dialog_role:await dialog.getAttribute('role'),dialog_name:await dialog.getAttribute('aria-label')}
})

matrixTest('chg34-notification-timestamp-contrast',async({page,proof})=>{
 await page.route('**/api/v1/notifications',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([
  {id:'uiqa-unread',title:'Unread notification',body:'Rendered contrast fixture',kind:'release',created_at:'2026-09-12T03:16:00Z',read_at:null},
  {id:'uiqa-read',title:'Read notification',body:'Rendered contrast fixture',kind:'audit',created_at:'2026-09-11T03:16:00Z',read_at:'2026-09-12T03:16:00Z'},
 ])}))
 await page.route('**/api/v1/notification-preferences',route=>route.fulfill({status:200,contentType:'application/json',body:'[]'}))
 await page.goto('/system');await page.getByRole('tab',{name:'Notifications',exact:true}).click();const modes:Record<string,unknown>={}
 for(const mode of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(mode);modes[mode]=[]
  if(mode==='light')await proof.prove('theme.light',async()=>expect(await page.getByLabel('Appearance',{exact:true}).inputValue()).toBe('light'))
  else await proof.prove('theme.dark',async()=>expect(await page.getByLabel('Appearance',{exact:true}).inputValue()).toBe('dark'))
  for(const timestamp of await page.locator('.system-list>article small').all())(modes[mode] as unknown[]).push(await contrastRatio(timestamp))
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high');await proof.prove('contrast.high',async()=>expect(page.locator('html')).toHaveAttribute('data-contrast','high'));const high=[]
 for(const timestamp of await page.locator('.system-list>article small').all())high.push(await contrastRatio(timestamp))
 const all=[...Object.values(modes).flat() as Array<{ratio:number}>,...high];await proof.prove('browser-computed',async()=>{expect(all.length).toBeGreaterThan(0);for(const result of all)expect(result.ratio).toBeGreaterThanOrEqual(4.5)})
 return {modes,high,timestamp_count:high.length}
})

matrixTest('chg34-work-items-loading',async({page,proof})=>{
 let release!:()=>void;const pending=new Promise<void>(resolvePromise=>{release=resolvePromise})
 await page.route('**/api/v1/work-items*',async route=>{await pending;await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(workItemPayload())})})
 await page.goto('/work-items',{waitUntil:'domcontentloaded'});await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024));await proof.prove('semantics.role-name-state',async()=>{const status=page.getByText('Loading records…',{exact:true});await expect(status).toBeVisible();expect(await status.getAttribute('role')).toBe('status')})
 const payload={status_role:await page.getByText('Loading records…',{exact:true}).getAttribute('role'),status_text:await page.getByText('Loading records…',{exact:true}).textContent(),shell_heading:await page.getByRole('heading',{name:'Work items',exact:true}).isVisible()}
 release();await expect(page.getByText('No matching records',{exact:true})).toBeVisible();return payload
})

matrixTest('chg34-work-items-empty',async({page,proof})=>{
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(workItemPayload())}));await workItemPage(page)
 const empty=page.getByRole('heading',{name:'No matching records',exact:true});await expect(empty).toBeVisible()
 await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024));await proof.prove('semantics.role-name-state',async()=>expect(empty).toBeVisible())
 return {heading:await empty.textContent(),empty_region:await empty.locator('..').getAttribute('class'),workspace_action:await page.getByRole('button',{name:/New work item/}).isVisible()}
})

matrixTest('chg34-work-items-error',async({page,proof})=>{
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'uiqa_fixture_error',message:'Deterministic UIQA error',request_id:'uiqa-error',details:null}})}));await workItemPage(page)
 const alert=page.getByRole('alert').filter({hasText:'Deterministic UIQA error'});await expect(alert).toBeVisible();await expect(alert.getByRole('button',{name:'Retry'})).toBeVisible()
 await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024));await proof.prove('semantics.role-name-state',async()=>{await expect(alert).toBeVisible();await expect(alert.getByRole('button',{name:'Retry'})).toBeVisible()})
 return {alert_role:await alert.getAttribute('role'),message:await alert.textContent(),retry_name:await alert.getByRole('button',{name:'Retry'}).getAttribute('aria-label')}
})

matrixTest('chg34-work-items-permission-readonly',async({page,proof})=>{
 await page.route('**/api/v1/bootstrap',async route=>{const response=await route.fetch();const body=await response.json();body.tenants=body.tenants.map((tenant:{permissions:string[]})=>({...tenant,permissions:[]}));await route.fulfill({response,json:body})})
 await workItemPage(page);await expect(page.getByText('Read only',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:/New work item/})).toHaveCount(0)
 const refresh=page.getByRole('button',{name:'Refresh workspace',exact:true})
 await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024));await proof.prove('semantics.role-name-state',async()=>expect(page.getByText('Read only',{exact:true})).toBeVisible());await proof.prove('browser-computed',async()=>expect(await page.getByRole('button',{name:/New work item/}).count()).toBe(0))
 return {access_text:await page.getByText('Read only',{exact:true}).textContent(),new_action_count:await page.getByRole('button',{name:/New work item/}).count(),refresh_visible:await refresh.isVisible(),refresh_disabled:await refresh.isDisabled()}
})

matrixTest('chg34-grid-row-selection',async({page,proof})=>{
 await workItemPage(page)
 const checkbox=page.getByRole('checkbox',{name:/Press Space to toggle row selection/}).first();const selectionCell=page.getByRole('gridcell',{name:/Press Space to toggle row selection/}).first();const selected=page.getByRole('region',{name:'Selected record actions'});const keyboardSequence:string[]=[]
 await proof.prove('viewport.desktop',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeGreaterThanOrEqual(1024))
 await proof.prove('semantics.role-name-state',async()=>{await expect(checkbox).toBeVisible();expect(await checkbox.getAttribute('type')).toBe('checkbox')})
 await proof.prove('keyboard.shift-tab',async()=>{await checkbox.focus();await page.keyboard.press('Shift+Tab');await expect(checkbox).not.toBeFocused();keyboardSequence.push('Shift+Tab')})
 await proof.prove('keyboard.tab',async()=>{await page.keyboard.press('Tab');await expect(selectionCell).toBeFocused();keyboardSequence.push('Tab')})
 await checkbox.focus();await expect(checkbox).toBeFocused()
 const focus=await checkbox.evaluate(element=>{const style=getComputedStyle(element);return {focus_visible:element.matches(':focus-visible'),outline:style.outline,outlineStyle:style.outlineStyle,outlineWidth:style.outlineWidth,outlineColor:style.outlineColor,outlineOffset:style.outlineOffset,boxShadow:style.boxShadow,active:document.activeElement===element}})
 await proof.prove('focus.visible',async()=>{expect(focus.focus_visible).toBe(true);expect(focus.outlineStyle).not.toBe('none');expect(Number.parseFloat(focus.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(focus.outlineOffset)).toBeGreaterThan(0);expect(focus.outlineColor).not.toBe('transparent')})
 await proof.prove('browser-computed',async()=>{expect(focus.active).toBe(true);expect(focus.outlineStyle).not.toBe('none');expect(Number.parseFloat(focus.outlineWidth)).toBeGreaterThan(0)})
 await proof.prove('keyboard.space',async()=>{await page.keyboard.press('Space');await expect(checkbox).toBeChecked();await expect(selected).toBeVisible();keyboardSequence.push('Space')})
 return {keyboard_sequence:keyboardSequence,keyboard_target:'row-selection-checkbox-cell',checkbox_role:await checkbox.getAttribute('role'),checked:await checkbox.isChecked(),selected_state:await selected.isVisible(),selected_region:await selected.getAttribute('aria-label'),focus_visible:focus.focus_visible,computed_focus_indicator:focus}
})

matrixTest('chg34-dialog-focus-recovery',async({page,proof})=>{
 await workItemPage(page);const trigger=page.getByRole('button',{name:'Save view',exact:true});await trigger.focus();await proof.prove('keyboard.enter',async()=>{await page.keyboard.press('Enter');await expect(page.getByRole('dialog',{name:'Save current view'})).toBeVisible()})
 const dialog=page.getByRole('dialog',{name:'Save current view'});await expect(dialog).toBeVisible();await proof.prove('semantics.role-name-state',async()=>{await expect(dialog).toHaveAttribute('aria-modal','true');await expect(dialog).toBeVisible()})
 const initialFocus=await page.evaluate(()=>({tag:document.activeElement?.tagName,name:(document.activeElement as HTMLElement|null)?.getAttribute('aria-label')}))
 const surfaceBody=dialog.locator('.surface-body');const close=dialog.getByRole('button',{name:'Close Save current view'})
 await close.focus();await proof.prove('keyboard.tab',async()=>{await page.keyboard.press('Tab');await expect(surfaceBody).toBeFocused()});await proof.prove('keyboard.shift-tab',async()=>{await page.keyboard.press('Shift+Tab');await expect(close).toBeFocused()})
 const focus=await close.evaluate(element=>{const style=getComputedStyle(element);return {focus_visible:element.matches(':focus-visible'),outline:style.outline,outlineStyle:style.outlineStyle,outlineWidth:style.outlineWidth,outlineColor:style.outlineColor,outlineOffset:style.outlineOffset,boxShadow:style.boxShadow,active:document.activeElement===element}})
 await proof.prove('focus.visible',async()=>{expect(focus.focus_visible).toBe(true);expect(focus.outlineStyle).not.toBe('none');expect(Number.parseFloat(focus.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(focus.outlineOffset)).toBeGreaterThan(0)})
 const ariaSnapshot=await dialog.ariaSnapshot();await proof.prove('keyboard.escape',async()=>{await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0)});await proof.prove('focus.recovery',async()=>expect(trigger).toBeFocused())
 return {initial_focus:initialFocus,aria_snapshot:ariaSnapshot,restored_focus:await page.evaluate(()=>({tag:document.activeElement?.tagName,name:(document.activeElement as HTMLElement|null)?.textContent}))}
})

matrixTest('chg34-reflow-320-css-px',async({page,proof})=>{
 await page.setViewportSize({width:320,height:800});await workItemPage(page)
 const heading=page.getByRole('heading',{name:'Work items',exact:true}),search=page.getByRole('textbox',{name:'Search records'}),action=page.getByRole('button',{name:/New work item/})
 await proof.prove('viewport.narrow',async()=>expect(await page.evaluate(()=>window.innerWidth)).toBeLessThan(760));await proof.prove('semantics.role-name-state',async()=>{await expect(heading).toBeVisible();await expect(search).toBeVisible();await expect(action).toBeVisible()})
 const overflow=await page.evaluate(()=>({viewport_css_px:document.documentElement.clientWidth,document_scroll_width:document.documentElement.scrollWidth,body_scroll_width:document.body.scrollWidth,document_scroll_height:document.documentElement.scrollHeight}))
 await proof.prove('reflow.320-css-px',async()=>{expect(overflow.viewport_css_px).toBe(320);expect(overflow.document_scroll_width).toBeLessThanOrEqual(overflow.viewport_css_px+1);expect(overflow.body_scroll_width).toBeLessThanOrEqual(overflow.viewport_css_px+1)})
 return {viewport:'320 CSS px',overflow,essential:{heading:await heading.isVisible(),search:await search.isVisible(),action:await action.isVisible()}}
})

matrixTest('chg34-reduced-motion',async({page,proof})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await workItemPage(page)
 const computed=await page.evaluate(()=>({media:window.matchMedia('(prefers-reduced-motion: reduce)').matches,transitions:[...document.querySelectorAll<HTMLElement>('button, a, input, .overlay-surface')].slice(0,20).map(element=>getComputedStyle(element).transitionDuration)}))
 await proof.prove('motion.reduced',async()=>expect(computed.media).toBe(true));await proof.prove('browser-computed',async()=>expect(computed.transitions.every(value=>Number.parseFloat(value)===0||Number.parseFloat(value)<=.01)).toBe(true));await proof.prove('semantics.role-name-state',async()=>expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible())
 return {computed,content_without_animation:await page.getByRole('heading',{name:'Work items',exact:true}).isVisible()}
})

matrixTest('chg34-forced-colors',async({page,proof})=>{
 await page.emulateMedia({forcedColors:'active'});await workItemPage(page);const action=page.getByRole('button',{name:/New work item/}).first();await action.focus();await proof.prove('keyboard.shift-tab',async()=>{await page.keyboard.press('Shift+Tab');await expect(action).not.toBeFocused()});await proof.prove('keyboard.tab',async()=>{await page.keyboard.press('Tab');await expect(action).toBeFocused()})
 const computed=await action.evaluate(element=>{const style=getComputedStyle(element);return {forcedColors:window.matchMedia('(forced-colors: active)').matches,focusVisible:element.matches(':focus-visible'),color:style.color,background:style.backgroundColor,outline:style.outline,outlineStyle:style.outlineStyle,outlineWidth:style.outlineWidth,outlineOffset:style.outlineOffset,visible:style.visibility,display:style.display}})
 await proof.prove('forced-colors.active',async()=>expect(computed.forcedColors).toBe(true));await proof.prove('focus.visible',async()=>{expect(computed.focusVisible).toBe(true);expect(computed.outlineStyle).not.toBe('none');expect(Number.parseFloat(computed.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(computed.outlineOffset)).toBeGreaterThan(0)});await proof.prove('browser-computed',async()=>{expect(computed.visible).not.toBe('hidden');expect(computed.display).not.toBe('none');expect(computed.color).not.toBe('rgba(0, 0, 0, 0)');expect(computed.background).not.toBe('rgba(0, 0, 0, 0)')});await proof.prove('semantics.role-name-state',async()=>expect(action).toBeVisible())
 return {computed,action_name:await action.textContent(),focus_visible:computed.focusVisible}
})

matrixTest('chg153-system-responsive-geometry',async({page,proof})=>{
 const candidate={candidate_sha:process.env.UIQA_CHECKOUT_COMMIT??null,candidate_tree:process.env.UIQA_CANDIDATE_TREE??null,candidate_version:process.env.UIQA_CANDIDATE_VERSION??null,browser:await page.evaluate(()=>navigator.userAgent)}
 const captures:Array<Record<string,unknown>>=[];let pointerWorked=false;let keyboardWorked=false
 for(const width of [1440,390,320]){
  const height=width===320?800:width===390?844:900;await page.setViewportSize({width,height});await page.goto('/system');await expect(page.getByRole('heading',{name:'System workspace',exact:true})).toBeVisible()
  const owner=page.getByRole('tablist',{name:'System sections'}),tabs=owner.getByRole('tab'),first=tabs.first(),middle=tabs.nth(Math.floor((await tabs.count())/2)),last=tabs.last();expect(await tabs.count()).toBe(9)
  const before=await pageGeometry(page);const ownerBefore=await owner.evaluate(element=>{const bounds=element.getBoundingClientRect(),style=getComputedStyle(element);return {clientWidth:element.clientWidth,scrollWidth:element.scrollWidth,left:bounds.left,right:bounds.right,overflowX:style.overflowX}})
  await first.click();await expect(first).toHaveAttribute('aria-selected','true');await pointerScrollToEnd(page,owner,last);const lastVisibleByPointer=await boxFullyInside(owner,last);await expect(last).toBeVisible();await last.click();await expect(last).toHaveAttribute('aria-selected','true');pointerWorked=pointerWorked||lastVisibleByPointer
  await first.click();await expect(first).toHaveAttribute('aria-selected','true')
  await page.evaluate(()=>{const target=document.querySelector('[role="tablist"]')!;let count=0;(window as unknown as {__uiqaTabClickCount:number}).__uiqaTabClickCount=0;target.addEventListener('click',()=>{count+=1;(window as unknown as {__uiqaTabClickCount:number}).__uiqaTabClickCount=count},{capture:true})})
  await first.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');await expect(first).toBeFocused();await page.waitForTimeout(20);const firstFocus=await focusEvidence(page,owner,first)
  for(let index=0;index<Math.floor((await tabs.count())/2);index+=1)await page.keyboard.press('Tab');await expect(middle).toBeFocused();await page.waitForTimeout(20);const middleFocus=await focusEvidence(page,owner,middle)
  for(let index=Math.floor((await tabs.count())/2);index<(await tabs.count())-1;index+=1)await page.keyboard.press('Tab');await expect(last).toBeFocused();await page.waitForTimeout(20);const finalFocus=await focusEvidence(page,owner,last)
  await page.keyboard.press('Enter');await expect(last).toHaveAttribute('aria-selected','true');const keyboardClickCount=await page.evaluate(()=>({count:(window as unknown as {__uiqaTabClickCount:number}).__uiqaTabClickCount,focusVisible:document.activeElement?.matches(':focus-visible')}));keyboardWorked=keyboardWorked||keyboardClickCount.count===1
  const controls=await owner.evaluate(element=>({tablistCount:document.querySelectorAll('[role="tablist"]').length,tabCount:element.querySelectorAll('[role="tab"]').length,visibleTabCount:[...element.querySelectorAll('[role="tab"]')].filter(control=>{const style=getComputedStyle(control);return style.display!=='none'&&style.visibility!=='hidden'&&control.getClientRects().length>0}).length,selected:[...element.querySelectorAll('[role="tab"]')].filter(control=>control.getAttribute('aria-selected')==='true').map(control=>control.textContent)}))
  expect(controls.tablistCount).toBe(1);expect(controls.tabCount).toBe(9);expect(controls.visibleTabCount).toBe(9);expect(controls.selected).toEqual(['Notifications']);expect(keyboardClickCount.count).toBe(1);expect(keyboardClickCount.focusVisible).toBe(true);for(const focus of [firstFocus,middleFocus,finalFocus]){expect(focus.active).toBe(true);expect(focus.focusVisible).toBe(true);expect(focus.outlineStyle).not.toBe('none');expect(Number.parseFloat(focus.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(focus.outlineOffset)).toBeGreaterThan(0);expect(focus.fully_inside_owner).toBe(true);expect(focus.fully_inside_viewport).toBe(true)}
  captures.push({width,height,role:'admin',active_section:await last.textContent(),page:before,owned_scroller:{before:ownerBefore,after:await owner.evaluate(element=>({scrollLeft:element.scrollLeft,clientWidth:element.clientWidth,scrollWidth:element.scrollWidth,overflowX:getComputedStyle(element).overflowX}))},pointer:{first:await first.textContent(),last:await last.textContent(),last_fully_visible_after_pointer_scroll:lastVisibleByPointer},keyboard:{first:{mode:await first.textContent(),focus:firstFocus},middle:{mode:await middle.textContent(),focus:middleFocus},final:{mode:await last.textContent(),focus:finalFocus},enter_click_count:keyboardClickCount.count,selected_tab:controls.selected[0]},controls})
  if(width===1440)await proof.prove('viewport.desktop',async()=>expect(before.viewport_css_px).toBe(1440))
  if(width===390)await proof.prove('viewport.narrow',async()=>expect(before.viewport_css_px).toBe(390))
  if(width===320)await proof.prove('reflow.320-css-px',async()=>{expect(before.viewport_css_px).toBe(320);expect(before.document_scroll_width).toBeLessThanOrEqual(320);expect(before.body_scroll_width).toBeLessThanOrEqual(320)})
 }
 const negative=await negativeControl(page);let pageContractFailed=false;let switchContractFailed=false;try{expect(negative.system.documentScrollWidth).toBeLessThanOrEqual(negative.system.viewport)}catch{pageContractFailed=true}try{expect(negative.visualization.lastFullyInside).toBe(true)}catch{switchContractFailed=true}
 const faultyFocus=negative.focusContainment.faulty,soundFocus=negative.focusContainment.sound;const focusContainmentFailed=faultyFocus.pageLevelOverflowGreen&&faultyFocus.focused&&!faultyFocus.fullyInsideOwner&&faultyFocus.partlyOutsideOwner;const focusContainmentSound=faultyFocus.pageLevelOverflowGreen&&soundFocus.pageLevelOverflowGreen&&soundFocus.fullyInsideOwner
 await proof.prove('semantics.role-name-state',async()=>expect((captures.every(capture=>(capture.controls as {tablistCount:number}).tablistCount===1))).toBe(true));await proof.prove('keyboard.tab',async()=>expect(keyboardWorked).toBe(true));await proof.prove('keyboard.enter',async()=>expect(keyboardWorked).toBe(true));await proof.prove('focus.visible',async()=>{for(const capture of captures){const keyboard=capture.keyboard as {first:{focus:{fully_inside_owner:boolean;fully_inside_viewport:boolean}};middle:{focus:{fully_inside_owner:boolean;fully_inside_viewport:boolean}};final:{focus:{fully_inside_owner:boolean;fully_inside_viewport:boolean}}};for(const target of [keyboard.first.focus,keyboard.middle.focus,keyboard.final.focus]){expect(target.fully_inside_owner).toBe(true);expect(target.fully_inside_viewport).toBe(true)}}});await proof.prove('input.pointer',async()=>expect(pointerWorked).toBe(true));await proof.prove('browser-computed',async()=>{expect(pageContractFailed).toBe(true);expect(switchContractFailed).toBe(true);expect(focusContainmentFailed).toBe(true);expect(focusContainmentSound).toBe(true);for(const capture of captures){const geometry=capture.page as Geometry;expect(geometry.document_scroll_width).toBeLessThanOrEqual(geometry.viewport_css_px);expect(geometry.body_scroll_width).toBeLessThanOrEqual(geometry.viewport_css_px)}})
 return {...candidate,surface:'/system',captures,negative_control_sensitivity:{page_contract_failed_on_unbounded_tablist:pageContractFailed,selector_contract_failed_on_clipped_switch:switchContractFailed,focus_containment_assertion_failed_on_faulty_fixture:focusContainmentFailed,focus_containment_sound_fixture_passed:focusContainmentSound,fixture:negative}}
})

matrixTest('chg153-visualization-responsive-geometry',async({page,proof})=>{
 test.setTimeout(180000)
 const candidate={candidate_sha:process.env.UIQA_CHECKOUT_COMMIT??null,candidate_tree:process.env.UIQA_CANDIDATE_TREE??null,candidate_version:process.env.UIQA_CANDIDATE_VERSION??null,browser:await page.evaluate(()=>navigator.userAgent)}
 const consumers=[{route:'/plan-tasks',name:'Planning'},{route:'/work-items',name:'Work items'},{route:'/incidents',name:'Incident command'}];const captures:Array<Record<string,unknown>>=[];let pointerWorked=false;let keyboardWorked=false
 const captureConsumer=async(route:string,name:string,width:number,height:number)=>{
  await page.setViewportSize({width,height});await page.goto(route);await page.evaluate(()=>localStorage.clear());await page.reload();try{await page.locator('.visualization-switch').waitFor({state:'visible',timeout:10000})}catch(error){throw new Error(`Visualization selector did not load for ${route} at ${width}px: ${String(error)}`)}const owner=page.getByRole('group',{name:'Visualization'}),buttons=owner.getByRole('button'),count=await buttons.count();expect(count).toBeGreaterThanOrEqual(3);const modes=await buttons.allTextContents(),first=buttons.first(),middle=buttons.nth(Math.floor(count/2)),last=buttons.last();const middleIndex=Math.floor(count/2);const before=await pageGeometry(page);const ownerBefore=await owner.evaluate(element=>{const bounds=element.getBoundingClientRect(),style=getComputedStyle(element);return {clientWidth:element.clientWidth,scrollWidth:element.scrollWidth,left:bounds.left,right:bounds.right,overflowX:style.overflowX}})
  await first.click();await expect(first).toHaveAttribute('aria-pressed','true');await expectRenderedMode(page,modes[0]!.toLowerCase());await pointerScrollToEnd(page,owner,last);const lastVisibleByPointer=await boxFullyInside(owner,last);await expect(last).toBeVisible();await last.click();await expect(last).toHaveAttribute('aria-pressed','true');await expect(page).toHaveURL(new RegExp(`[?&]visualization=${encodeURIComponent(modes.at(-1)!.toLowerCase())}(?:&|$)`));await expectRenderedMode(page,modes.at(-1)!.toLowerCase());pointerWorked=pointerWorked||lastVisibleByPointer
  await page.goto(route);await page.evaluate(()=>localStorage.clear());await page.reload();await page.locator('.visualization-switch').waitFor({state:'visible'});const keyboardOwner=page.getByRole('group',{name:'Visualization'}),keyboardButtons=keyboardOwner.getByRole('button'),keyboardFirst=keyboardButtons.first(),keyboardMiddle=keyboardButtons.nth(middleIndex),keyboardLast=keyboardButtons.last();await keyboardFirst.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');await expect(keyboardFirst).toBeFocused();await page.waitForTimeout(20);const firstFocus=await focusEvidence(page,keyboardOwner,keyboardFirst);for(let index=0;index<middleIndex;index+=1)await page.keyboard.press('Tab');await expect(keyboardMiddle).toBeFocused();await page.waitForTimeout(20);const middleFocus=await focusEvidence(page,keyboardOwner,keyboardMiddle)
  await page.evaluate(()=>{const state=window as unknown as {__uiqaSwitchClickCount:number;__uiqaSwitchHistoryCount:number;__uiqaSwitchHistoryPatched?:boolean};state.__uiqaSwitchClickCount=0;state.__uiqaSwitchHistoryCount=0;const owner=document.querySelector('[aria-label="Visualization"]')!;owner.addEventListener('click',event=>{if((event.target as HTMLElement).closest('button'))state.__uiqaSwitchClickCount+=1},{capture:true});if(!state.__uiqaSwitchHistoryPatched){const pushState=history.pushState,replaceState=history.replaceState;history.pushState=((...args)=>{state.__uiqaSwitchHistoryCount+=1;return pushState.apply(history,args)}) as History['pushState'];history.replaceState=((...args)=>{state.__uiqaSwitchHistoryCount+=1;return replaceState.apply(history,args)}) as History['replaceState'];state.__uiqaSwitchHistoryPatched=true}})
  await page.keyboard.press('Enter');await expect(keyboardMiddle).toHaveAttribute('aria-pressed','true');await expect(page).toHaveURL(new RegExp(`[?&]visualization=${encodeURIComponent(modes[middleIndex]!.toLowerCase())}(?:&|$)`));await expectRenderedMode(page,modes[middleIndex]!.toLowerCase());const middleActivation=await page.evaluate(()=>{const state=window as unknown as {__uiqaSwitchClickCount:number;__uiqaSwitchHistoryCount:number};return {click_count:state.__uiqaSwitchClickCount,history_change_count:state.__uiqaSwitchHistoryCount,url:location.href}});expect(middleActivation.click_count).toBe(1);expect(middleActivation.history_change_count).toBe(1)
  await keyboardFirst.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');for(let index=0;index<count-1;index+=1)await page.keyboard.press('Tab');await expect(keyboardLast).toBeFocused();await page.waitForTimeout(20);const finalFocus=await focusEvidence(page,keyboardOwner,keyboardLast);await page.evaluate(()=>{const state=window as unknown as {__uiqaSwitchClickCount:number;__uiqaSwitchHistoryCount:number};state.__uiqaSwitchClickCount=0;state.__uiqaSwitchHistoryCount=0;const owner=document.querySelector('[aria-label="Visualization"]')!;owner.addEventListener('click',event=>{if((event.target as HTMLElement).closest('button'))state.__uiqaSwitchClickCount+=1},{capture:true})});await page.keyboard.press('Enter');await expect(keyboardLast).toHaveAttribute('aria-pressed','true');await expect(page).toHaveURL(new RegExp(`[?&]visualization=${encodeURIComponent(modes.at(-1)!.toLowerCase())}(?:&|$)`));await expectRenderedMode(page,modes.at(-1)!.toLowerCase());const finalActivation=await page.evaluate(()=>{const state=window as unknown as {__uiqaSwitchClickCount:number;__uiqaSwitchHistoryCount:number};return {click_count:state.__uiqaSwitchClickCount,history_change_count:state.__uiqaSwitchHistoryCount,url:location.href}});expect(finalActivation.click_count).toBe(1);expect(finalActivation.history_change_count).toBe(1);keyboardWorked=keyboardWorked||firstFocus.fully_inside_owner&&middleFocus.fully_inside_owner&&finalFocus.fully_inside_owner
  const hiddenState=await keyboardOwner.evaluate(element=>({ownerCount:document.querySelectorAll('.visualization-switch-scroll').length,buttonCount:element.querySelectorAll('button').length,operableButtons:[...element.querySelectorAll('button')].filter(button=>{const style=getComputedStyle(button);return style.display!=='none'&&style.visibility!=='hidden'&&button.getAttribute('aria-hidden')!=='true'}).length,scrollLeft:element.scrollLeft,scrollWidth:element.scrollWidth,clientWidth:element.clientWidth}));for(const focus of [firstFocus,middleFocus,finalFocus]){expect(focus.active).toBe(true);expect(focus.focusVisible).toBe(true);expect(focus.outlineStyle).not.toBe('none');expect(Number.parseFloat(focus.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(focus.outlineOffset)).toBeGreaterThan(0);expect(focus.fully_inside_owner).toBe(true);expect(focus.fully_inside_viewport).toBe(true)};expect(hiddenState.ownerCount).toBe(1);expect(hiddenState.buttonCount).toBe(hiddenState.operableButtons)
  captures.push({consumer:name,route,width,height,available_modes:modes,active_mode:modes.at(-1),url:page.url(),page:before,owned_scroller:{before:ownerBefore,after:hiddenState},pointer:{first:modes[0],middle:modes[middleIndex],last:modes.at(-1),last_fully_visible_after_pointer_scroll:lastVisibleByPointer},keyboard:{first:{mode:modes[0],focus:firstFocus},middle:{mode:modes[middleIndex],focus:middleFocus,activation:middleActivation},final:{mode:modes.at(-1),focus:finalFocus,activation:finalActivation}},hidden_responsive_controls:hiddenState})
 }
 await page.setViewportSize({width:1440,height:900});await page.goto('/plan-tasks');await page.locator('.visualization-switch').waitFor({state:'visible'});const desktopOwner=page.getByRole('group',{name:'Visualization'}),desktopButtons=desktopOwner.getByRole('button');await proof.prove('viewport.desktop',async()=>expect((await pageGeometry(page)).viewport_css_px).toBe(1440));captures.push({consumer:'Planning',route:'/plan-tasks',width:1440,height:900,page:await pageGeometry(page),owned_scroller:await desktopOwner.evaluate(element=>({clientWidth:element.clientWidth,scrollWidth:element.scrollWidth,overflowX:getComputedStyle(element).overflowX})),available_modes:await desktopButtons.allTextContents(),active_mode:await desktopButtons.filter({hasText:/./}).evaluateAll(elements=>elements.find(element=>element.getAttribute('aria-pressed')==='true')?.textContent)})
 for(const consumer of consumers)for(const width of [390,320])await captureConsumer(consumer.route,consumer.name,width,width===320?800:844)
 await proof.prove('viewport.narrow',async()=>expect((captures.find(capture=>capture.width===390)?.page as Geometry).viewport_css_px).toBe(390));await proof.prove('reflow.320-css-px',async()=>{for(const capture of captures.filter(value=>value.width===320)){const geometry=capture.page as Geometry;expect(geometry.viewport_css_px).toBe(320);expect(geometry.document_scroll_width).toBeLessThanOrEqual(320);expect(geometry.body_scroll_width).toBeLessThanOrEqual(320)}})
 await page.setViewportSize({width:390,height:844});await page.goto('/plan-tasks');await page.evaluate(()=>localStorage.clear());await page.reload();const planningOwner=page.getByRole('group',{name:'Visualization'}),gantt=planningOwner.getByRole('button',{name:'Gantt',exact:true}),search=page.getByRole('textbox').first();await search.waitFor({state:'visible'});await gantt.click();await search.fill('task');await page.waitForTimeout(350);const filter=page.locator('.command-bar select').first();let filterValue:string|null=null;if(await filter.count()&&await filter.locator('option').count()>1){await filter.selectOption({index:1});filterValue=await filter.inputValue()}await page.setViewportSize({width:1440,height:900});await page.waitForTimeout(100);await page.setViewportSize({width:390,height:844});await expect(gantt).toHaveAttribute('aria-pressed','true');await expect(search).toHaveValue('task');if(filterValue!==null)await expect(filter).toHaveValue(filterValue);const preserved={mode:await gantt.getAttribute('aria-pressed'),search:await search.inputValue(),filter:filterValue,url:page.url(),summary:await page.locator('.workspace-summary').getByText('gantt',{exact:true}).isVisible()}
 await page.emulateMedia({forcedColors:'active'});await page.setViewportSize({width:390,height:420});await page.goto('/plan-tasks');await page.evaluate(()=>localStorage.clear());await page.reload();await page.locator('.visualization-switch').waitFor({state:'visible'});const shortOwner=page.getByRole('group',{name:'Visualization'}),shortButtons=shortOwner.getByRole('button'),shortFirst=shortButtons.first(),shortLast=shortButtons.last();await shortFirst.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');for(let index=0;index<(await shortButtons.count())-1;index+=1)await page.keyboard.press('Tab');await expect(shortLast).toBeFocused();await page.waitForTimeout(20);const forcedFocus={...(await focusEvidence(page,shortOwner,shortLast)),forcedColors:await page.evaluate(()=>window.matchMedia('(forced-colors: active)').matches)};await page.keyboard.press('Enter');await expect(shortLast).toHaveAttribute('aria-pressed','true');const shortGeometry=await pageGeometry(page);await proof.prove('forced-colors.active',async()=>expect(forcedFocus.forcedColors).toBe(true));await proof.prove('focus.visible',async()=>{expect(forcedFocus.active).toBe(true);expect(forcedFocus.focusVisible).toBe(true);expect(forcedFocus.outlineStyle).not.toBe('none');expect(Number.parseFloat(forcedFocus.outlineWidth)).toBeGreaterThan(0);expect(Number.parseFloat(forcedFocus.outlineOffset)).toBeGreaterThan(0);expect(forcedFocus.fully_inside_owner).toBe(true);expect(forcedFocus.fully_inside_viewport).toBe(true)});await proof.prove('semantics.role-name-state',async()=>{expect(await hiddenResponsiveCount(page)).toBe(0);expect(await shortOwner.count()).toBe(1);expect(await shortButtons.count()).toBeGreaterThanOrEqual(3)})
 const negative=await negativeControl(page);let switchContractFailed=false;try{expect(negative.visualization.lastFullyInside).toBe(true)}catch{switchContractFailed=true};const faultyFocus=negative.focusContainment.faulty,soundFocus=negative.focusContainment.sound;const focusContainmentFailed=faultyFocus.pageLevelOverflowGreen&&faultyFocus.focused&&!faultyFocus.fullyInsideOwner&&faultyFocus.partlyOutsideOwner;const focusContainmentSound=faultyFocus.pageLevelOverflowGreen&&soundFocus.pageLevelOverflowGreen&&soundFocus.fullyInsideOwner;await proof.prove('input.pointer',async()=>expect(pointerWorked).toBe(true));await proof.prove('keyboard.tab',async()=>expect(keyboardWorked).toBe(true));await proof.prove('keyboard.enter',async()=>expect(keyboardWorked).toBe(true));await proof.prove('browser-computed',async()=>{expect(shortGeometry.document_scroll_width).toBeLessThanOrEqual(390);expect(shortGeometry.body_scroll_width).toBeLessThanOrEqual(390);expect(switchContractFailed).toBe(true);expect(focusContainmentFailed).toBe(true);expect(focusContainmentSound).toBe(true);for(const capture of captures.filter(value=>typeof value.width==='number'&&value.width!==1440)){const geometry=capture.page as Geometry;expect(geometry.document_scroll_width).toBeLessThanOrEqual(geometry.viewport_css_px);expect(geometry.body_scroll_width).toBeLessThanOrEqual(geometry.viewport_css_px)}})
 return {...candidate,surface:'EntityWorkspace visualization selector',consumers:consumers.map(consumer=>consumer.name),captures,responsive_state_preservation:preserved,short_height_forced_colors:{viewport:{width:390,height:420},geometry:shortGeometry,focus:forcedFocus},hidden_responsive_controls:'single owner; inactive modes are not duplicated or aria-hidden operable',negative_control_sensitivity:{selector_contract_failed_on_clipped_switch:switchContractFailed,focus_containment_assertion_failed_on_faulty_fixture:focusContainmentFailed,focus_containment_sound_fixture_passed:focusContainmentSound,fixture:negative}}
})

async function hiddenResponsiveCount(page:Page):Promise<number>{return page.locator('.visualization-switch-scroll').evaluateAll(elements=>elements.reduce((count,element)=>count+[...element.querySelectorAll('button')].filter(button=>{const style=getComputedStyle(button);return style.display==='none'||style.visibility==='hidden'||button.getAttribute('aria-hidden')==='true'}).length,0))}
