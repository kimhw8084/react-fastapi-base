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
