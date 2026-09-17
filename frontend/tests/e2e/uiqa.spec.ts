import {createHash} from 'node:crypto'
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs'
import {basename,dirname,resolve} from 'node:path'
import {test,expect,type Page,type TestInfo} from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

type MatrixRow={state_id:string;material_state_class:string;required_dimensions:string[];browser_test_id:string;required_evidence:{artifact_locators:string[];axe_serious_critical:boolean}}
const root=resolve(process.cwd(),'..')
const matrixFile=resolve(process.cwd(),'tests/e2e/ui-state-matrix.json')
const matrix=JSON.parse(readFileSync(matrixFile,'utf8')) as {matrix_id:string;rows:MatrixRow[]}
const rows=matrix.rows
const rowByState=new Map(rows.map(row=>[row.state_id,row]))
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

function matrixTest(stateId:string,body:(args:{page:Page},row:MatrixRow,info:TestInfo)=>Promise<Record<string,unknown>>):void{
 const row=rowFor(stateId)
 test(`${row.browser_test_id} ${row.state_id}`,async({page},info)=>{
  info.annotations.push({type:'ui-matrix-state',description:row.state_id})
  const payload=await body({page},row,info)
  const axe=row.required_evidence.axe_serious_critical?await axeSummary(page):undefined
  await writeStateEvidence(row,page,{...payload,...(axe?{axe}: {})})
 })
}

test.afterEach(({},info)=>{
 const stateId=info.annotations.find(annotation=>annotation.type==='ui-matrix-state')?.description
 if(!stateId)return
 const row=rowFor(stateId)
 results.push({state_id:stateId,browser_test_id:row.browser_test_id,status:info.status===info.expectedStatus?'PASS':'FAIL',exercised_dimensions:[...row.required_dimensions].sort(),artifact_locators:[...row.required_evidence.artifact_locators].sort()})
})

test.afterAll(()=>{
 mkdirSync(dirname(resultsFile),{recursive:true})
 const ordered=[...results].sort((left,right)=>left.state_id.localeCompare(right.state_id))
 const manifest={
  schema_version:1,
  result_kind:'browser-computed-uiqa',
  matrix_id:matrix.matrix_id,
  matrix_sha256:createHash('sha256').update(readFileSync(matrixFile)).digest('hex'),
  source_commit:process.env.UIQA_SOURCE_COMMIT??null,
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

matrixTest('chg34-theme-operations-primary-action',async({page},row)=>{
 await workItemPage(page)
 await page.getByLabel('Appearance',{exact:true}).selectOption('dark')
 await page.getByLabel('Theme',{exact:true}).selectOption('operations')
 const primary=page.locator('button.primary').first();const result=await contrastRatio(primary)
 expect(result.ratio).toBeGreaterThanOrEqual(4.5)
 return {computed_contrast:result,semantic_name:await primary.getAttribute('aria-label'),theme:await page.locator('html').getAttribute('data-theme'),artifact_hint:basename(row.required_evidence.artifact_locators[0]!)}
})

matrixTest('chg34-grid-semantic-theme-modes',async({page})=>{
 await workItemPage(page)
 const grid=page.getByLabel('Work items data grid');const modes:Record<string,unknown>={}
 for(const appearance of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(appearance);await expect(grid).toBeVisible()
  modes[appearance]=await grid.evaluate(element=>{
   const root=element.querySelector('.ag-root-wrapper')!,header=element.querySelector('.ag-header')!,row=element.querySelector('.ag-row')!
   const style=(node:Element)=>{const computed=getComputedStyle(node);return {background:computed.backgroundColor,color:computed.color}}
   return {root:style(root),header:style(header),row:style(row),rows:element.querySelectorAll('.ag-row').length}
  })
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high');await expect(page.locator('html')).toHaveAttribute('data-contrast','high')
 const high=await grid.locator('.ag-row').first().evaluate(element=>({background:getComputedStyle(element).backgroundColor,color:getComputedStyle(element).color}))
 expect((modes.dark as {root:{background:string}}).root.background).not.toBe('rgb(255, 255, 255)')
 expect((modes.light as {root:{background:string;row:{background:string}}}).root.background).toBe((modes.light as {root:{background:string;row:{background:string}}}).row.background)
 expect(high.background).toBe('rgb(0, 0, 0)');expect(high.color).toBe('rgb(255, 255, 255)')
 expect((modes.light as {row:{color:string}}).row.color).not.toBe('rgb(24, 29, 31)')
 expect((modes.light as {rows:number}).rows).toBeLessThanOrEqual(55)
 return {computed_modes:modes,computed_high_contrast:high,grid_role:await grid.getAttribute('role'),grid_name:await grid.getAttribute('aria-label')}
})

matrixTest('chg34-saved-view-checkbox-selection',async({page})=>{
 await workItemPage(page);await page.getByRole('button',{name:'Save view',exact:true}).click()
 const dialog=page.getByRole('dialog',{name:'Save current view'});const controls=[]
 for(const name of ['Favorite','Default for this workspace']){
  const checkbox=dialog.getByRole('checkbox',{name})
  const geometry=await checkbox.evaluate(element=>{const label=element.closest('label')!;const style=getComputedStyle(label);const bounds=element.getBoundingClientRect();return {display:style.display,direction:style.flexDirection,width:Math.round(bounds.width),height:Math.round(bounds.height),native:element instanceof HTMLInputElement}})
  expect(geometry).toMatchObject({display:'flex',direction:'row',width:16,height:16,native:true})
  await checkbox.focus();await expect(checkbox).toBeFocused();await page.keyboard.press('Space');await expect(checkbox).toBeChecked()
  controls.push({name,geometry,checked:await checkbox.isChecked(),role:await checkbox.getAttribute('role')})
 }
 return {controls,dialog_role:await dialog.getAttribute('role'),dialog_name:await dialog.getAttribute('aria-label')}
})

matrixTest('chg34-notification-timestamp-contrast',async({page})=>{
 await page.route('**/api/v1/notifications',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([
  {id:'uiqa-unread',title:'Unread notification',body:'Rendered contrast fixture',kind:'release',created_at:'2026-09-12T03:16:00Z',read_at:null},
  {id:'uiqa-read',title:'Read notification',body:'Rendered contrast fixture',kind:'audit',created_at:'2026-09-11T03:16:00Z',read_at:'2026-09-12T03:16:00Z'},
 ])}))
 await page.route('**/api/v1/notification-preferences',route=>route.fulfill({status:200,contentType:'application/json',body:'[]'}))
 await page.goto('/system');await page.getByRole('tab',{name:'Notifications',exact:true}).click();const modes:Record<string,unknown>={}
 for(const mode of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(mode);modes[mode]=[]
  for(const timestamp of await page.locator('.system-list>article small').all())(modes[mode] as unknown[]).push(await contrastRatio(timestamp))
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high');const high=[]
 for(const timestamp of await page.locator('.system-list>article small').all())high.push(await contrastRatio(timestamp))
 const all=[...Object.values(modes).flat() as Array<{ratio:number}>,...high];expect(all.length).toBeGreaterThan(0)
 for(const result of all)expect(result.ratio).toBeGreaterThanOrEqual(4.5)
 return {modes,high,timestamp_count:high.length}
})

matrixTest('chg34-work-items-loading',async({page})=>{
 let release!:()=>void;const pending=new Promise<void>(resolvePromise=>{release=resolvePromise})
 await page.route('**/api/v1/work-items*',async route=>{await pending;await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(workItemPayload())})})
 await page.goto('/work-items',{waitUntil:'domcontentloaded'});await expect(page.getByText('Loading records…',{exact:true})).toBeVisible()
 const payload={status_role:await page.getByText('Loading records…',{exact:true}).getAttribute('role'),status_text:await page.getByText('Loading records…',{exact:true}).textContent(),shell_heading:await page.getByRole('heading',{name:'Work items',exact:true}).isVisible()}
 release();await expect(page.getByText('No matching records',{exact:true})).toBeVisible();return payload
})

matrixTest('chg34-work-items-empty',async({page})=>{
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(workItemPayload())}));await workItemPage(page)
 const empty=page.getByRole('heading',{name:'No matching records',exact:true});await expect(empty).toBeVisible()
 return {heading:await empty.textContent(),empty_region:await empty.locator('..').getAttribute('class'),workspace_action:await page.getByRole('button',{name:/New work item/}).isVisible()}
})

matrixTest('chg34-work-items-error',async({page})=>{
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'uiqa_fixture_error',message:'Deterministic UIQA error',request_id:'uiqa-error',details:null}})}));await workItemPage(page)
 const alert=page.getByRole('alert').filter({hasText:'Deterministic UIQA error'});await expect(alert).toBeVisible();await expect(alert.getByRole('button',{name:'Retry'})).toBeVisible()
 return {alert_role:await alert.getAttribute('role'),message:await alert.textContent(),retry_name:await alert.getByRole('button',{name:'Retry'}).getAttribute('aria-label')}
})

matrixTest('chg34-work-items-permission-readonly',async({page})=>{
 await page.route('**/api/v1/bootstrap',async route=>{const response=await route.fetch();const body=await response.json();body.tenants=body.tenants.map((tenant:{permissions:string[]})=>({...tenant,permissions:[]}));await route.fulfill({response,json:body})})
 await workItemPage(page);await expect(page.getByText('Read only',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:/New work item/})).toHaveCount(0)
 const refresh=page.getByRole('button',{name:'Refresh workspace',exact:true})
 return {access_text:await page.getByText('Read only',{exact:true}).textContent(),new_action_count:await page.getByRole('button',{name:/New work item/}).count(),refresh_visible:await refresh.isVisible(),refresh_disabled:await refresh.isDisabled()}
})

matrixTest('chg34-grid-row-selection',async({page})=>{
 await workItemPage(page);const checkbox=page.getByRole('checkbox',{name:/Select/}).first();await checkbox.check();await expect(checkbox).toBeChecked()
 const selected=page.getByRole('region',{name:'Selected record actions'});await expect(selected).toBeVisible()
 const focus=await checkbox.evaluate(element=>{const style=getComputedStyle(element);return {outline:style.outline,outlineColor:style.outlineColor,boxShadow:style.boxShadow,active:document.activeElement===element}})
 return {checkbox_role:await checkbox.getAttribute('role'),checked:await checkbox.isChecked(),selected_region:await selected.getAttribute('aria-label'),focus}
})

matrixTest('chg34-dialog-focus-recovery',async({page})=>{
 await workItemPage(page);const trigger=page.getByRole('button',{name:'Save view',exact:true});await trigger.focus();await page.keyboard.press('Enter')
 const dialog=page.getByRole('dialog',{name:'Save current view'});await expect(dialog).toBeVisible()
 const initialFocus=await page.evaluate(()=>({tag:document.activeElement?.tagName,name:(document.activeElement as HTMLElement|null)?.getAttribute('aria-label')}))
 const firstFocusable=dialog.locator('button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled])').first()
 await expect(firstFocusable).toBeFocused();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');await expect(firstFocusable).toBeFocused()
 const ariaSnapshot=await dialog.ariaSnapshot();await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(trigger).toBeFocused()
 return {initial_focus:initialFocus,aria_snapshot:ariaSnapshot,restored_focus:await page.evaluate(()=>({tag:document.activeElement?.tagName,name:(document.activeElement as HTMLElement|null)?.textContent}))}
})

matrixTest('chg34-reflow-320-css-px',async({page})=>{
 await page.setViewportSize({width:320,height:800});await workItemPage(page)
 const heading=page.getByRole('heading',{name:'Work items',exact:true}),search=page.getByRole('textbox',{name:'Search records'}),action=page.getByRole('button',{name:/New work item/})
 await expect(heading).toBeVisible();await expect(search).toBeVisible();await expect(action).toBeVisible()
 const overflow=await page.evaluate(()=>({viewport_css_px:document.documentElement.clientWidth,document_scroll_width:document.documentElement.scrollWidth,body_scroll_width:document.body.scrollWidth,document_scroll_height:document.documentElement.scrollHeight}))
 expect(overflow.document_scroll_width).toBeLessThanOrEqual(overflow.viewport_css_px+1);expect(overflow.body_scroll_width).toBeLessThanOrEqual(overflow.viewport_css_px+1)
 return {viewport:'320 CSS px',overflow,essential:{heading:await heading.isVisible(),search:await search.isVisible(),action:await action.isVisible()}}
})

matrixTest('chg34-reduced-motion',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await workItemPage(page)
 const computed=await page.evaluate(()=>({media:window.matchMedia('(prefers-reduced-motion: reduce)').matches,transitions:[...document.querySelectorAll<HTMLElement>('button, a, input, .overlay-surface')].slice(0,20).map(element=>getComputedStyle(element).transitionDuration)}))
 expect(computed.media).toBe(true);expect(computed.transitions.every(value=>Number.parseFloat(value)===0||Number.parseFloat(value)<=.01)).toBe(true)
 return {computed,content_without_animation:await page.getByRole('heading',{name:'Work items',exact:true}).isVisible()}
})

matrixTest('chg34-forced-colors',async({page})=>{
 await page.emulateMedia({forcedColors:'active'});await workItemPage(page);const action=page.getByRole('button',{name:/New work item/}).first();await action.focus()
 const computed=await action.evaluate(element=>{const style=getComputedStyle(element);return {forcedColors:window.matchMedia('(forced-colors: active)').matches,color:style.color,background:style.backgroundColor,outline:style.outline,visible:style.visibility,display:style.display}})
 expect(computed.forcedColors).toBe(true);expect(computed.visible).not.toBe('hidden');expect(computed.display).not.toBe('none')
 return {computed,action_name:await action.textContent(),focus_visible:await action.evaluate(element=>document.activeElement===element)}
})
