import {mkdir,writeFile} from 'node:fs/promises'
import {chromium} from 'playwright'

const root=new URL('../..',import.meta.url).pathname
const appBase=process.env.UIQA_APP_BASE??'http://127.0.0.1:5173'
const labBase=process.env.UIQA_LAB_BASE??'http://127.0.0.1:4173'
const output=process.env.UIQA_OUTPUT??`${root}/evidence/current/uiqa/CHG-6-r1-rendered.json`

const contrast=locator=>locator.evaluate(element=>{
 const rgba=value=>{const match=value.match(/rgba?\(([^)]+)\)/);if(!match)return null;const parts=match[1].split(',').map(Number);return parts.length<3?null:[parts[0],parts[1],parts[2],parts[3]??1]}
 const linear=value=>{const channel=value/255;return channel<=.03928?channel/12.92:((channel+.055)/1.055)**2.4}
 const luminance=value=>.2126*linear(value[0])+.7152*linear(value[1])+.0722*linear(value[2])
 const foreground=rgba(getComputedStyle(element).color)??[0,0,0,1];let node=element;let background=[255,255,255,1]
 while(node){const value=rgba(getComputedStyle(node).backgroundColor);if(value&&value[3]>0){background=value;break}node=node.parentElement}
 const foregroundL=luminance(foreground),backgroundL=luminance(background)
 return {ratio:Number(((Math.max(foregroundL,backgroundL)+.05)/(Math.min(foregroundL,backgroundL)+.05)).toFixed(2)),foreground,background}
})

const allContrasts=async locator=>Promise.all(await locator.all().then(items=>items.map(item=>contrast(item))))
const appContext=await chromium.launch({headless:true})
const app=await appContext.newPage({viewport:{width:1440,height:1000}})
await app.goto(`${appBase}/`);await app.locator('.golden-grid').waitFor()
await app.getByLabel('Appearance',{exact:true}).selectOption('dark');await app.getByLabel('Theme',{exact:true}).selectOption('operations')
const accent=await contrast(app.locator('button.primary').first())
const grid=await app.locator('.golden-grid').evaluate(element=>{
 const describe=selector=>{const node=element.querySelector(selector);const style=getComputedStyle(node);return {background:style.backgroundColor,color:style.color}}
 return {wrapperClass:element.className,root:describe('.ag-root-wrapper'),header:describe('.ag-header'),row:describe('.ag-row'),renderedRows:element.querySelectorAll('.ag-row').length}
})
await app.goto(`${appBase}/work-items`);await app.getByRole('button',{name:'Save view',exact:true}).click()
const savedViews=await app.getByRole('dialog',{name:'Save current view'}).locator('input[type="checkbox"]').evaluateAll(elements=>elements.map(element=>{const label=element.closest('label'),style=getComputedStyle(label);const bounds=element.getBoundingClientRect();return {name:label.textContent.trim(),display:style.display,flexDirection:style.flexDirection,width:Math.round(bounds.width),height:Math.round(bounds.height),native:element instanceof HTMLInputElement}}))
await appContext.close()

const notifications=[{id:'uiqa-unread',title:'Unread notification',body:'Rendered contrast fixture',kind:'release',created_at:'2026-09-12T03:16:00Z',read_at:null},{id:'uiqa-read',title:'Read notification',body:'Rendered contrast fixture',kind:'audit',created_at:'2026-09-11T03:16:00Z',read_at:'2026-09-12T03:16:00Z'}]
const notificationRatios={}
// A separate browser context per mode prevents persisted theme preferences from masking the fixture.
const browser=await chromium.launch({headless:true})
for(const mode of ['light','dark','high']){
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage()
 await page.route('**/api/v1/notifications',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(notifications)}))
 await page.route('**/api/v1/notification-preferences',route=>route.fulfill({status:200,contentType:'application/json',body:'[]'}))
 await page.goto(`${appBase}/system`);await page.getByRole('tab',{name:'Notifications',exact:true}).click()
 if(mode==='high')await page.getByLabel('Contrast',{exact:true}).selectOption('high')
 else await page.getByLabel('Appearance',{exact:true}).selectOption(mode)
 notificationRatios[mode]=await allContrasts(page.locator('.system-list>article small'))
 await context.close()
}
await browser.close()

const labBrowser=await chromium.launch({headless:true})
const lab={}
for(const theme of ['light','dark'])for(const highContrast of [false,true]){
 const context=await labBrowser.newContext({viewport:{width:1440,height:1100}}),page=await context.newPage()
 await page.goto(`${labBase}/#/themes`)
 if(theme==='dark')await page.getByRole('button',{name:'Toggle light and dark theme'}).click()
 if(highContrast)await page.getByLabel('High contrast',{exact:true}).check()
 await page.goto(`${labBase}/#/timeline`)
 const key=`${theme}-${highContrast?'high':'normal'}`
 lab[key]={infoBadge:await contrast(page.locator('.badge.tone-info').first()),stateBlocks:await allContrasts(page.locator('.state-block'))}
 await page.goto(`${labBase}/#/traces`);lab[key].traceBars=await allContrasts(page.locator('.trace-bar'))
 await page.goto(`${labBase}/#/notifications`);lab[key].timestamps=await allContrasts(page.locator('.notification-item small'))
 await context.close()
}
await labBrowser.close()

await mkdir(new URL('.',`file://${output}`).pathname,{recursive:true})
await writeFile(output,JSON.stringify({project:'react-fastapi-base',change:'CHG-6',iteration:1,base_sha:'68b55ee1dd3fda00d8899682b4f8a09733f3dd0b',version:'1.0.0-rc.7',generated_at:new Date().toISOString(),app:{darkOperationsAccent:accent,agGrid:grid,savedViews,notificationTimestamps:notificationRatios},experienceLab:lab},null,2)+'\n')
console.log(output)
