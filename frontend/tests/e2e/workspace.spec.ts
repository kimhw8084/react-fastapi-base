import {test,expect} from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('create, reload and retrieve revision-backed details',async({page})=>{
 await page.goto('/')
 await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 await page.getByRole('button',{name:/New work item/}).click()
 const dialog=page.getByRole('dialog',{name:'New work item'})
 const title=`Browser reference ${Date.now()}`
 await dialog.getByRole('textbox',{name:/Title/}).fill(title)
 await dialog.getByRole('textbox',{name:'Description'}).fill('Persistent, auditable browser acceptance fixture.')
 await dialog.getByRole('button',{name:'Save changes'}).click()
 await expect(page.getByRole('dialog',{name:title})).toBeVisible()
 await page.reload()
 await expect(page.getByRole('dialog',{name:title})).toBeVisible()
 for(const tab of ['Relationships','Activity','History','Compare','Comments','Files','Audit','Actions']){
  await page.getByRole('button',{name:tab,exact:true}).click()
  await expect(page.getByRole('dialog',{name:title})).toBeVisible()
 }
 await page.getByRole('button',{name:'History',exact:true}).click()
 await expect(page.getByRole('region',{name:'Version history'})).toContainText('Revision 1')
 await page.getByRole('button',{name:'Compare',exact:true}).click()
 await expect(page.getByRole('region',{name:'Compare revisions'})).toBeVisible()
})

test('dirty form close requires a decision',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:/New work item/}).click()
 const dialog=page.getByRole('dialog',{name:'New work item'})
 await dialog.getByRole('textbox',{name:/Title/}).fill('Do not lose this draft')
 await dialog.getByRole('button',{name:'Cancel',exact:true}).click()
 await expect(page.getByRole('dialog',{name:'Discard unsaved changes?'})).toBeVisible()
 await page.getByRole('button',{name:'Keep editing'}).click()
 await expect(dialog.getByRole('textbox',{name:/Title/})).toHaveValue('Do not lose this draft')
})

test('dirty form protects browser Back navigation',async({page})=>{
 await page.goto('/projects');await page.getByRole('link',{name:'Work items',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 await page.getByRole('button',{name:/New work item/}).click()
 const dialog=page.getByRole('dialog',{name:'New work item'})
 await dialog.getByRole('textbox',{name:/Title/}).fill('Keep this draft on Back')
 const prompt=page.waitForEvent('dialog')
 const back=page.goBack({waitUntil:'commit'})
 const browserDialog=await prompt
 expect(browserDialog.message()).toBe('You have unsaved changes. Leave this page and discard them?')
 await browserDialog.dismiss()
 await back
 await expect(page).toHaveURL(/\/work-items/)
 await expect(page.getByRole('dialog',{name:'New work item'})).toBeVisible()
})

test('team saved views persist scope, favorite and default metadata',async({page})=>{
 await page.goto('/work-items')
 await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Save view',exact:true}).click()
 const dialog=page.getByRole('dialog',{name:'Save current view'})
 const name=`Browser saved view ${Date.now()}`
 await dialog.getByRole('textbox',{name:'Name'}).fill(name)
 await dialog.getByLabel('Visibility').selectOption('team')
 await dialog.getByRole('checkbox',{name:/Favorite/}).check()
 await dialog.getByRole('checkbox',{name:/Default/}).check()
 await dialog.getByRole('button',{name:'Save view',exact:true}).click()
 await expect(page.getByLabel('Saved views')).toContainText(name)
 await expect(page.getByLabel('Saved views')).toContainText('★')
})

test('admin can manage membership-scoped workspace teams',async({page})=>{
 await page.goto('/system')
 await expect(page.getByRole('heading',{name:'System workspace',exact:true})).toBeVisible()
 await page.getByRole('tab',{name:'Teams',exact:true}).click()
 const teamName=`Browser team ${Date.now()}`,slug=`browser-team-${Date.now()}`
 await page.getByRole('textbox',{name:'Team name'}).fill(teamName)
 await page.getByRole('textbox',{name:'Team slug'}).fill(slug)
 await page.getByRole('button',{name:'Create team'}).click()
 const team=page.getByRole('article').filter({hasText:teamName})
 await expect(team).toContainText('1 explicit members')
 await team.getByRole('textbox',{name:`Add member to ${teamName}`}).fill('browser.member')
 await team.getByRole('button',{name:'Add member'}).click()
 await expect(team).toContainText('2 explicit members')
 await page.getByRole('tab',{name:'Events',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Durable event stream',exact:true})).toBeVisible()
 await expect(page.getByRole('region',{name:'Durable events'})).toBeVisible()
})

test('registered workspaces load without browser errors',async({page})=>{
 const consoleErrors:string[]=[]
 const pageErrors:string[]=[]
 page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text())})
 page.on('pageerror',error=>pageErrors.push(error.message))
 const routes=['work-items','projects','racks','equipment','knowledge-entries','investigations','research','risks','plan-tasks','diagram-documents','process-measurements','wafer-runs','manufacturing-lots','equipment-states','process-recipes','software-services','delivery-runs','observability-events','incidents','service-objectives','system']
 for(const route of routes){
  await page.goto(`/${route}`)
  await expect(page.locator('main, [role="main"]').first()).toBeVisible()
  await expect(page.getByText('Page not found',{exact:true})).toHaveCount(0)
 }
 expect(pageErrors).toEqual([])
 expect(consoleErrors).toEqual([])
})

test('representative mobile surfaces remain keyboard and axe clean',async({page})=>{
 await page.setViewportSize({width:390,height:844})
 const consoleErrors:string[]=[]
 page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text())})
 for(const route of ['/work-items','/plan-tasks?visualization=gantt','/diagram-documents?visualization=designer','/system']){
  await page.goto(route)
  await expect(page.locator('main, [role="main"]').first()).toBeVisible()
  const firstFocusable=page.locator('button:visible, a:visible, input:visible, select:visible, textarea:visible, [tabindex="0"]:visible').first()
  await expect(firstFocusable).toBeVisible()
  await firstFocusable.focus()
  expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY')
  await page.keyboard.press('Tab')
  expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY')
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
  expect(result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([])
 }
 expect(consoleErrors).toEqual([])
})

test('100k logical table scope stays bounded to the server page',async({page},info)=>{
 const items=Array.from({length:50},(_,index)=>({id:`logical-${index}`,title:`Logical record ${index}`,description:'',status:index%2?'open':'done',priority:'normal',revision:1,archived:false,created_by:'demo.admin',created_at:'2026-09-09T00:00:00Z',updated_at:'2026-09-09T00:00:00Z'}))
 await page.route('**/api/v1/work-items*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({items,total:100000,limit:50,offset:0})}))
 const started=await page.evaluate(()=>performance.now())
 await page.goto('/work-items')
 await expect(page.locator('.workspace-summary > div').filter({hasText:'Matching records'}).getByRole('strong')).toHaveText('100000')
 await expect(page.getByLabel('Work items data grid')).toBeVisible()
 const renderedRows=await page.locator('.ag-row').count()
 const elapsed=await page.evaluate(start=>performance.now()-start,started)
 const memory=await page.evaluate(()=>{const performanceWithMemory=performance as Performance&{memory?:{usedJSHeapSize:number}};return performanceWithMemory.memory?.usedJSHeapSize??null})
 await info.attach('table-100k-browser-performance.json',{body:Buffer.from(JSON.stringify({logical_rows:100000,server_page:50,rendered_rows:renderedRows,elapsed_ms:Math.round(elapsed),used_js_heap_bytes:memory},null,2)),contentType:'application/json'})
 expect(renderedRows).toBeLessThanOrEqual(55)
 expect(elapsed).toBeLessThan(5000)
})

test('major workspaces remain axe clean under high contrast, reduced motion and zoom',async({page},info)=>{
 await page.emulateMedia({reducedMotion:'reduce'})
 await page.setViewportSize({width:1280,height:900})
 const routes=['/','/work-items','/projects','/racks','/plan-tasks?visualization=gantt','/diagram-documents?visualization=designer','/knowledge-entries','/investigations','/risks','/research','/process-measurements','/wafer-runs','/manufacturing-lots','/equipment-states','/process-recipes','/software-services','/delivery-runs','/observability-events','/incidents','/service-objectives','/system']
 const reports:Record<string,unknown>={}
 for(const route of routes){
  await page.goto(route)
  await expect(page.locator('main, [role="main"]').first()).toBeVisible()
  if(route==='/'){
   await page.getByLabel('Contrast',{exact:true}).selectOption('high')
  }
  await expect(page.locator('html')).toHaveAttribute('data-contrast','high')
  await page.evaluate(()=>{document.documentElement.style.zoom='2'})
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
  reports[route]={serious_or_critical:result.violations.filter(v=>v.impact==='serious'||v.impact==='critical').map(v=>v.id),total:result.violations.length,zoom:'200%',reduced_motion:'reduce',contrast:await page.locator('html').getAttribute('data-contrast')}
  expect(result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([])
  await page.evaluate(()=>{document.documentElement.style.zoom='4'})
  await expect(page.locator('main, [role="main"]').first()).toBeVisible()
  await page.evaluate(()=>{document.documentElement.style.zoom=''})
 }
 await info.attach('major-surfaces-axe.json',{body:Buffer.from(JSON.stringify(reports,null,2)),contentType:'application/json'})
})

for(const theme of ['Operations','Clarity','Minimal'])test(`theme ${theme}: no serious/critical automated accessibility violations`,async({page},info)=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 await page.getByLabel('Theme',{exact:true}).selectOption({label:theme})
 await expect(page.locator('html')).toHaveAttribute('data-theme',theme.toLowerCase())
 const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
 await info.attach('axe.json',{body:Buffer.from(JSON.stringify(result,null,2)),contentType:'application/json'})
 await info.attach('theme.png',{body:await page.screenshot({fullPage:true}),contentType:'image/png'})
 expect(result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([])
})
