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
 await page.getByRole('button',{name:'History',exact:true}).click()
 await expect(page.getByRole('region',{name:'Version history'})).toContainText('Revision 1')
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

for(const theme of ['Operations','Clarity','Minimal'])test(`theme ${theme}: no serious/critical automated accessibility violations`,async({page},info)=>{
 await page.goto('/');await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 await page.getByLabel('Theme',{exact:true}).selectOption({label:theme})
 await expect(page.locator('html')).toHaveAttribute('data-theme',theme.toLowerCase())
 const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
 await info.attach('axe.json',{body:Buffer.from(JSON.stringify(result,null,2)),contentType:'application/json'})
 await info.attach('theme.png',{body:await page.screenshot({fullPage:true}),contentType:'image/png'})
 expect(result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([])
})
