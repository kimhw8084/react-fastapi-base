import {test,expect} from '@playwright/test'

const contrastRatio=async(locator:ReturnType<import('@playwright/test').Page['locator']>)=>locator.evaluate(element=>{
 const rgb=(value:string)=>{const match=value.match(/rgba?\(([^)]+)\)/);if(!match)return null;const parts=match[1]!.split(',').map(Number);return parts.length<3?null:[parts[0]!,parts[1]!,parts[2]!,parts[3]??1]}
 const linear=(value:number)=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4}
 const luminance=(value:number[])=>.2126*linear(value[0]!)+.7152*linear(value[1]!)+.0722*linear(value[2]!)
 const foreground=rgb(getComputedStyle(element).color)??[0,0,0,1]
 let node:Element|null=element;let background:number[]=[255,255,255,1]
 while(node){const value=rgb(getComputedStyle(node).backgroundColor);if(value&&value[3]!>0){background=value;break}node=node.parentElement}
 const fgL=luminance(foreground),bgL=luminance(background)
 return {ratio:(Math.max(fgL,bgL)+.05)/(Math.min(fgL,bgL)+.05),foreground,background}
})

test('UIQA-001 dark Operations accent text meets AA contrast',async({page})=>{
 await page.goto('/')
 await page.getByLabel('Appearance',{exact:true}).selectOption('dark')
 await page.getByLabel('Theme',{exact:true}).selectOption('operations')
 const result=await contrastRatio(page.locator('button.primary').first())
 expect(result.ratio).toBeGreaterThanOrEqual(4.5)
})

test('UIQA-002 v36 grid uses semantic dark/light/high-contrast theme and stays virtualized',async({page})=>{
 await page.goto('/work-items')
 const grid=page.getByLabel('Work items data grid')
 for(const appearance of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(appearance)
  await expect(grid).toBeVisible()
  const result=await grid.evaluate(element=>{
   const root=element.querySelector('.ag-root-wrapper')!,header=element.querySelector('.ag-header')!,row=element.querySelector('.ag-row')!
   const style=(node:Element)=>{const computed=getComputedStyle(node);return {background:computed.backgroundColor,color:computed.color}}
   return {root:style(root),header:style(header),row:style(row),rows:element.querySelectorAll('.ag-row').length}
  })
  if(appearance==='dark')expect(result.root.background).not.toBe('rgb(255, 255, 255)')
  expect(result.root.background).toBe(result.row.background)
  expect(result.row.color).not.toBe('rgb(24, 29, 31)')
  expect(result.rows).toBeLessThanOrEqual(55)
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high')
 await expect(page.locator('html')).toHaveAttribute('data-contrast','high')
 const high=await grid.locator('.ag-row').first().evaluate(element=>({background:getComputedStyle(element).backgroundColor,color:getComputedStyle(element).color}))
 expect(high.background).toBe('rgb(0, 0, 0)')
 expect(high.color).toBe('rgb(255, 255, 255)')
})

test('UIQA-003 Saved View native checkbox grouping and keyboard semantics remain intact',async({page})=>{
 await page.goto('/work-items')
 await page.getByRole('button',{name:'Save view',exact:true}).click()
 const dialog=page.getByRole('dialog',{name:'Save current view'})
 for(const name of ['Favorite','Default for this workspace']){
  const checkbox=dialog.getByRole('checkbox',{name})
  expect(await checkbox.evaluate(element=>{const label=element.closest('label');const style=getComputedStyle(label!);const bounds=element.getBoundingClientRect();return {display:style.display,direction:style.flexDirection,width:Math.round(bounds.width),height:Math.round(bounds.height),native:element instanceof HTMLInputElement}})).toMatchObject({display:'flex',direction:'row',width:16,height:16,native:true})
  await checkbox.focus()
  await expect(checkbox).toBeFocused()
  await page.keyboard.press('Space')
  await expect(checkbox).toBeChecked()
 }
})

test('UIQA-007 app notification timestamps meet AA on light, dark and high contrast surfaces',async({page})=>{
 await page.route('**/api/v1/notifications',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify([
  {id:'uiqa-unread',title:'Unread notification',body:'Rendered contrast fixture',kind:'release',created_at:'2026-09-12T03:16:00Z',read_at:null},
  {id:'uiqa-read',title:'Read notification',body:'Rendered contrast fixture',kind:'audit',created_at:'2026-09-11T03:16:00Z',read_at:'2026-09-12T03:16:00Z'},
 ])}))
 await page.route('**/api/v1/notification-preferences',route=>route.fulfill({status:200,contentType:'application/json',body:'[]'}))
 await page.goto('/system')
 await page.getByRole('tab',{name:'Notifications',exact:true}).click()
 for(const mode of ['light','dark']){
  await page.getByLabel('Appearance',{exact:true}).selectOption(mode)
  for(const timestamp of await page.locator('.system-list>article small').all())expect((await contrastRatio(timestamp)).ratio).toBeGreaterThanOrEqual(4.5)
 }
 await page.getByLabel('Contrast',{exact:true}).selectOption('high')
 for(const timestamp of await page.locator('.system-list>article small').all())expect((await contrastRatio(timestamp)).ratio).toBeGreaterThanOrEqual(4.5)
})
