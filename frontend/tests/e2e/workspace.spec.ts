import {test,expect,type Page} from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

async function waitForHighContrastPaint(page:Page){
 await page.waitForFunction(()=>{
  const root=document.documentElement,heading=document.querySelector('.page-heading h1')
  if(root.dataset.contrast!=='high'||!root.dataset.theme||!root.dataset.mode||!heading)return false
  const rootStyle=getComputedStyle(root),bodyStyle=getComputedStyle(document.body),headingColor=getComputedStyle(heading).color
  return rootStyle.getPropertyValue('--surface-page').trim()==='#000'&&rootStyle.getPropertyValue('--text-primary').trim()==='#fff'&&bodyStyle.backgroundColor==='rgb(0, 0, 0)'&&headingColor==='rgb(255, 255, 255)'
 },undefined,{timeout:10000})
}

function readThemePaint(){
 const root=document.documentElement,rootStyle=getComputedStyle(root),bodyStyle=getComputedStyle(document.body)
 const transparent=(color:string)=>color==='transparent'||color==='rgba(0, 0, 0, 0)'
 const ancestors=(element:Element)=>{const result:Array<{tag:string;selector:string;color:string;backgroundColor:string;backgroundImage:string}>=[];for(let node:Element|null=element;node&&result.length<8;node=node.parentElement){const style=getComputedStyle(node);result.push({tag:node.tagName,selector:node.id?`#${node.id}`:typeof node.className==='string'?node.className.split(/\s+/).filter(Boolean).map(name=>`.${name}`).join(''):'',color:style.color,backgroundColor:style.backgroundColor,backgroundImage:style.backgroundImage})}return result}
 const headingStyles=['.page-heading .eyebrow','.page-heading h1','.page-heading p'].map(selector=>{const element=document.querySelector(selector);if(!element)return{selector,missing:true};const style=getComputedStyle(element),chain=ancestors(element);return{selector,color:style.color,backgroundColor:style.backgroundColor,fontSize:style.fontSize,fontWeight:style.fontWeight,nearestOpaqueAncestor:chain.find(node=>!transparent(node.backgroundColor))??{source:'canvas'},ancestors:chain}})
 const stylesheets=[...document.styleSheets].map(sheet=>{let ruleCount=0,highContrastRule=false;try{const rules=[...sheet.cssRules];ruleCount=rules.length;highContrastRule=rules.some(rule=>rule.cssText.includes('data-contrast'))}catch{}return{path:sheet.href?new URL(sheet.href).pathname:null,disabled:sheet.disabled,ruleCount,highContrastRule}})
 return{url:location.pathname,attributes:{theme:root.dataset.theme??null,mode:root.dataset.mode??null,contrast:root.dataset.contrast??null},media:{prefersDark:matchMedia('(prefers-color-scheme: dark)').matches,prefersLight:matchMedia('(prefers-color-scheme: light)').matches,prefersReducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches},html:{color:rootStyle.color,backgroundColor:rootStyle.backgroundColor,backgroundImage:rootStyle.backgroundImage,semantic:Object.fromEntries(['--surface-page','--surface-sidebar','--surface-panel','--text-primary','--text-secondary','--text-muted','--accent','--danger','--warning','--success','--focus'].map(name=>[name,rootStyle.getPropertyValue(name).trim()]))},body:{color:bodyStyle.color,backgroundColor:bodyStyle.backgroundColor,backgroundImage:bodyStyle.backgroundImage},effectiveCanvasBackground:!transparent(bodyStyle.backgroundColor)?bodyStyle.backgroundColor:(!transparent(rootStyle.backgroundColor)?rootStyle.backgroundColor:'browser-default'),headings:headingStyles,stylesheets}
}

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
  await page.getByRole('tab',{name:tab,exact:true}).click()
  await expect(page.getByRole('dialog',{name:title})).toBeVisible()
 }
 await page.getByRole('tab',{name:'History',exact:true}).click()
 await expect(page.getByRole('region',{name:'Version history'})).toContainText('Revision 1')
 await page.getByRole('tab',{name:'Compare',exact:true}).click()
 await expect(page.getByRole('region',{name:'Compare revisions'})).toBeVisible()
})

test('read-only viewer dossier comments do not expose a composer',async({page})=>{
 await page.goto('/')
 await page.getByRole('button',{name:/New work item/}).click()
 const dialog=page.getByRole('dialog',{name:'New work item'})
 const title=`Viewer comments ${Date.now()}`
 await dialog.getByRole('textbox',{name:/Title/}).fill(title)
 await dialog.getByRole('button',{name:'Save changes'}).click()
 await expect(page.getByRole('dialog',{name:title})).toBeVisible()
 await page.route('**/api/v1/bootstrap',async route=>{
  const response=await route.fetch();const body=await response.json()
  body.user_id='victor';body.tenants=body.tenants.map((tenant:{permissions:string[]})=>({...tenant,permissions:['read']}))
  await route.fulfill({response,json:body})
 })
 await page.reload()
  await page.getByRole('tab',{name:'Comments',exact:true}).click()
 await expect(page.getByText('Comments are read-only for this record.',{exact:true})).toBeVisible()
 await expect(page.getByRole('textbox',{name:'Add comment'})).toHaveCount(0)
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

test('major workspaces remain axe clean under high contrast, reduced motion and zoom',async({page},info)=>{
 await page.emulateMedia({reducedMotion:'reduce'})
 await page.setViewportSize({width:1280,height:900})
 const routes=['/','/work-items','/projects','/racks','/plan-tasks?visualization=gantt','/diagram-documents?visualization=designer','/knowledge-entries','/investigations','/risks','/research','/process-measurements','/wafer-runs','/manufacturing-lots','/equipment-states','/process-recipes','/software-services','/delivery-runs','/observability-events','/incidents','/service-objectives','/system']
  const reports:Record<string,unknown>={}
 try{
  for(const route of routes){
   await page.goto(route)
   await expect(page.locator('main, [role="main"]').first()).toBeVisible()
   if(route==='/'){
    const theme=page.locator('#desktop-theme');await expect(theme).toBeVisible();await expect(theme).toHaveAccessibleName('Theme');await theme.selectOption('operations')
    const contrast=page.locator('#desktop-contrast');await expect(contrast).toBeVisible();await expect(contrast).toHaveAccessibleName('Contrast');await contrast.selectOption('high')
   }
   await expect(page.locator('html')).toHaveAttribute('data-contrast','high')
   await waitForHighContrastPaint(page)
   const before=route==='/system'?await page.evaluate(readThemePaint):undefined
   const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
   const serious=result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')
   const after=route==='/system'?await page.evaluate(readThemePaint):undefined
   reports[route]={serious_or_critical:serious.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,checks:n.any.map(check=>({message:check.message,data:check.data}))}))})),total:result.violations.length,zoom:'100%',reduced_motion:'reduce',contrast:await page.locator('html').getAttribute('data-contrast'),...(route==='/system'?{computed_before_axe:before,computed_after_axe:after}:{})}
   if(route==='/system'||serious.length){
    await info.attach('major-workspaces-axe-progress.json',{body:Buffer.from(JSON.stringify(reports,null,2)),contentType:'application/json'})
    await info.attach(`major-workspaces-${route==='/system'?'system':'failure'}.png`,{body:await page.screenshot(),contentType:'image/png'})
   }
   expect(serious,`${route} serious/critical axe violations`).toEqual([])
   await page.evaluate(()=>{document.documentElement.style.zoom='2'})
   await expect(page.locator('main, [role="main"]').first()).toBeVisible()
   await page.evaluate(()=>{document.documentElement.style.zoom='4'})
   await expect(page.locator('main, [role="main"]').first()).toBeVisible()
   await page.evaluate(()=>{document.documentElement.style.zoom=''})
  }
 }finally{
  try{reports.last_observed_state=await page.evaluate(readThemePaint)}catch{}
  await info.attach('major-surfaces-axe.json',{body:Buffer.from(JSON.stringify(reports,null,2)),contentType:'application/json'})
  try{await info.attach('major-surfaces-final.png',{body:await page.screenshot(),contentType:'image/png'})}catch{}
 }
})

for(const theme of ['Operations','Clarity','Minimal'])test(`theme ${theme}: no serious/critical automated accessibility violations`,async({page},info)=>{
 await page.setViewportSize({width:1280,height:900});await page.goto('/');await expect(page.getByRole('heading',{name:'Work items',exact:true})).toBeVisible()
 const themeControl=page.locator('#desktop-theme');await expect(themeControl).toBeVisible();await expect(themeControl).toHaveAccessibleName('Theme');await themeControl.selectOption({label:theme})
 await expect(page.locator('html')).toHaveAttribute('data-theme',theme.toLowerCase())
 const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()
 await info.attach('axe.json',{body:Buffer.from(JSON.stringify(result,null,2)),contentType:'application/json'})
 await info.attach('theme.png',{body:await page.screenshot({fullPage:true}),contentType:'image/png'})
 expect(result.violations.filter(v=>v.impact==='serious'||v.impact==='critical')).toEqual([])
})
