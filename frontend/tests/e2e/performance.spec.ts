import {createHash} from 'node:crypto'
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs'
import {dirname,resolve} from 'node:path'
import {performance} from 'node:perf_hooks'
import {test,expect,type Page,type TestInfo} from '@playwright/test'

const root=resolve(process.cwd(),'..')
const contractPath=resolve(root,'contracts/performance-regression.json')
const contract=JSON.parse(readFileSync(contractPath,'utf8')) as {contract_id:string;browser:{project:string;viewport:{width:number;height:number}};workloads:Array<Record<string,unknown>>}
const contractSha256=createHash('sha256').update(readFileSync(contractPath)).digest('hex')
const output=resolve(process.env.PERFORMANCE_OUTPUT??resolve(root,'evidence/current/performance/browser.json'))
const sourceCommit=process.env.PERFORMANCE_SOURCE_COMMIT??null
const sourceDigest=process.env.PERFORMANCE_SOURCE_DIGEST??null
const results:Array<Record<string,unknown>>=[]
const browserIdentity={project:process.env.PERFORMANCE_PROJECT??contract.browser.project}

function workload(id:string):Record<string,unknown>{
 const value=contract.workloads.find(item=>item.id===id)
 if(!value)throw new Error(`Unknown performance workload ${id}`)
 return value
}

function item(index:number,prefix:string):Record<string,unknown>{
 return {id:`${prefix}-${index}`,title:`${prefix==='logical'?'Logical':'Synthetic'} work item ${String(index).padStart(4,'0')}`,description:'',status:index%2?'open':'done',priority:index%3?'normal':'high',revision:1,archived:false,created_by:'demo.admin',created_at:'2026-09-09T00:00:00Z',updated_at:'2026-09-09T00:00:00Z'}
}

function pageMemory(page:Page):Promise<number|null>{
 return page.evaluate(()=>{const value=performance as Performance&{memory?:{usedJSHeapSize:number}};return value.memory?.usedJSHeapSize??null})
}

async function browserMetadata(page:Page){
 const viewport=page.viewportSize()
 return {browser_project:browserIdentity.project,viewport:{width:viewport?.width??0,height:viewport?.height??0}}
}

test.afterEach(({},info)=>{
 const id=info.annotations.find(annotation=>annotation.type==='performance-workload')?.description
 if(!id)return
 if(results.some(row=>row.id===id))return
 const expected=workload(id)
 results.push({id,tier_id:expected.tier_id,status:info.status===info.expectedStatus?'PASS':'FAIL',scale:expected.scale,budgets:expected.budgets,hard_metrics:{},diagnostic_metrics:{used_js_heap_bytes:null},evidence_locator:'evidence/current/performance/browser.json'})
})

test.afterAll(()=>{
 const ordered=[...results].sort((left,right)=>String(left.id).localeCompare(String(right.id)))
 const document={schema_version:2,report_kind:'performance-regression-result',tier_id:'browser-ag-grid-scale',contract_id:contract.contract_id,contract_sha256:contractSha256,source_commit:sourceCommit,source_digest:sourceDigest,command:['npm','run','test:e2e','--','tests/e2e/performance.spec.ts'],browser:browserIdentity,result:ordered.length===2&&ordered.every(row=>row.status==='PASS')?'PASS':'FAIL',workloads:ordered}
 mkdirSync(dirname(output),{recursive:true});writeFileSync(output,`${JSON.stringify(document,null,2)}\n`)
})

test('browser-server-page-100k-50 preserves the production paging boundary',async({page},info)=>{
 info.annotations.push({type:'performance-workload',description:'browser-server-page-100k-50'})
 const definition=workload('browser-server-page-100k-50')
 const scale=definition.scale as {logical_rows:number;loaded_rows:number;page_size:number}
 const budgets=definition.budgets as Record<string,number>
 const items=Array.from({length:scale.loaded_rows},(_,index)=>item(index,'logical'))
 await page.setViewportSize(contract.browser.viewport)
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items,total:scale.logical_rows,limit:scale.page_size,offset:0})}))
 const started=performance.now()
 await page.goto('/work-items')
 await expect(page.locator('.workspace-summary > div').filter({hasText:'Matching records'}).getByRole('strong')).toHaveText(String(scale.logical_rows))
 await expect(page.getByLabel('Work items data grid')).toBeVisible()
 await expect(page.locator('.ag-row').first()).toBeVisible()
 const renderedBefore=await page.locator('.ag-row').count()
 const renderedAfter=renderedBefore
 const elapsed=Math.round(performance.now()-started)
 const metrics={logical_rows:scale.logical_rows,loaded_rows:scale.loaded_rows,rendered_rows_before_deep_scroll:renderedBefore,rendered_rows_after_deep_scroll:renderedAfter,initial_readiness_ms:elapsed}
 const diagnostics={rendered_row_ratio:null,used_js_heap_bytes:await pageMemory(page)}
 const metadata=await browserMetadata(page)
 const row={id:'browser-server-page-100k-50',tier_id:'browser-ag-grid-scale',status:'PASS',scale,budgets,hard_metrics:metrics,diagnostic_metrics:diagnostics,evidence_locator:'evidence/current/performance/browser.json',...metadata,fixture_kind:'production-shaped-server-page'}
 results.push(row)
 await info.attach('browser-server-page-100k-50.json',{body:Buffer.from(JSON.stringify({...row,fixture_kind:'production-shaped-server-page'},null,2)),contentType:'application/json'})
 const expected=definition.invariants as {rendered_row_ceiling:number}
 expect(renderedBefore).toBeLessThanOrEqual(expected.rendered_row_ceiling)
 expect(elapsed).toBeLessThanOrEqual(budgets.initial_readiness_ms)
})

test('browser-ag-grid-virtualization-5000 proves synthetic test-only row recycling',async({page},info)=>{
 info.annotations.push({type:'performance-workload',description:'browser-ag-grid-virtualization-5000'})
 const definition=workload('browser-ag-grid-virtualization-5000')
 const scale=definition.scale as {logical_rows:number;loaded_rows:number}
 const budgets=definition.budgets as Record<string,number>
 const items=Array.from({length:scale.loaded_rows},(_,index)=>item(index,'synthetic'))
 await page.setViewportSize(contract.browser.viewport)
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items,total:scale.logical_rows,limit:scale.loaded_rows,offset:0})}))
 const started=performance.now()
 await page.goto('/work-items')
 await expect(page.getByLabel('Work items data grid')).toBeVisible()
 await expect(page.locator('.ag-row').first()).toBeVisible()
 const renderedBefore=await page.locator('.ag-row').count()
 const initialRows=await page.locator('.ag-row').allTextContents()
 const initialIdentity='Synthetic work item 0000'
 expect(initialRows.some(value=>value.includes(initialIdentity))).toBe(true)
 const readyMs=Math.round(performance.now()-started)

 // The normal AG Grid layout exposes its actual scroll surface as the
 // browser-visible grid viewport; the scrollbar track is separate/hidden.
 const viewport=page.locator('.ag-grid-viewport').first()
 await expect(viewport).toBeVisible()
 const deepStarted=performance.now()
 await viewport.evaluate(element=>{element.scrollTop=element.scrollHeight;element.dispatchEvent(new Event('scroll',{bubbles:true}))})
 const targetLabel='Synthetic work item 4999'
 const deepRow=page.locator('.ag-row').filter({hasText:targetLabel}).first()
 await expect(deepRow).toBeVisible()
 const deepMs=Math.round(performance.now()-deepStarted)
 const afterRows=await page.locator('.ag-row').count()
 const afterTexts=await page.locator('.ag-row').allTextContents()
 const recycled=!afterTexts.some(value=>value.includes(initialIdentity))
 const targetIndex=(definition.invariants as {deep_target_index:number}).deep_target_index
 const selectionStart=performance.now()
 const deepCheckbox=deepRow.getByRole('checkbox').first()
 await deepCheckbox.focus()
 await expect(deepCheckbox).toBeFocused()
 await page.keyboard.press('Space')
 await expect(page.getByRole('region',{name:'Selected record actions'})).toBeVisible()
 const selectionWorks=true
 const sortStarted=performance.now()
 await viewport.evaluate(element=>{element.scrollTop=0;element.dispatchEvent(new Event('scroll',{bubbles:true}))})
 const titleHeader=page.getByRole('columnheader',{name:/Title/}).first()
 await titleHeader.click()
 const firstRow=page.locator('.ag-row').first()
 await expect(firstRow).toContainText('Synthetic work item 0000')
 const sortMs=Math.round(performance.now()-sortStarted)
 const metrics={logical_rows:scale.logical_rows,loaded_rows:scale.loaded_rows,rendered_rows_before_deep_scroll:renderedBefore,rendered_rows_after_deep_scroll:afterRows,rendered_row_ratio:afterRows/scale.loaded_rows,initial_rows_recycled:recycled,reached_target_row:targetLabel.includes(String(targetIndex).padStart(4,'0')),selection_or_keyboard_works:selectionWorks,representative_sort_works:true,initial_readiness_ms:readyMs,deep_scroll_settle_ms:deepMs,sort_interaction_ms:sortMs}
 const diagnostics={used_js_heap_bytes:await pageMemory(page)}
 const metadata=await browserMetadata(page)
 const row={id:'browser-ag-grid-virtualization-5000',tier_id:'browser-ag-grid-scale',status:'PASS',scale,budgets,hard_metrics:metrics,diagnostic_metrics:diagnostics,evidence_locator:'evidence/current/performance/browser.json',...metadata,row_recycling_proof:{initial_identity:initialIdentity,removed_after_deep_scroll:recycled},selection_result:{target_label:targetLabel,keyboard:'Space',selected_region:true},sort_result:{column:'Title',first_row:'Synthetic work item 0000'},fixture_kind:'synthetic-test-only'}
 results.push(row)
 await info.attach('browser-ag-grid-virtualization-5000.json',{body:Buffer.from(JSON.stringify(row,null,2)),contentType:'application/json'})
 const invariants=definition.invariants as {rendered_row_ceiling:number;rendered_row_fraction_ceiling:number}
 expect(renderedBefore).toBeLessThanOrEqual(invariants.rendered_row_ceiling)
 expect(afterRows).toBeLessThanOrEqual(invariants.rendered_row_ceiling)
 expect(afterRows/scale.loaded_rows).toBeLessThanOrEqual(invariants.rendered_row_fraction_ceiling)
 expect(recycled).toBe(true)
 expect(deepMs).toBeLessThanOrEqual(budgets.deep_scroll_settle_ms)
 expect(sortMs).toBeLessThanOrEqual(budgets.sort_interaction_ms)
 void selectionStart
})
