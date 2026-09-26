import {test,expect,type Browser,type BrowserContext,type Page,type TestInfo} from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
test.use({trace:'on'})

type Scheme='light'|'dark'
type Screenshot={name:string;body:Buffer}
type Evidence={source:Record<string,string|undefined>;browser:string;system_preference:Scheme;reduced_motion:'reduce';appearance:'system';theme:'operations';contrast:'high';route_observations:unknown[];axe_cases:Array<{label:string;before:unknown;after:unknown;serious_or_critical:unknown[];other_violation_ids:string[]}>;negative_control?:unknown;error?:string}
const tags=['wcag2a','wcag2aa','wcag21aa','wcag22aa']

function readThemePaint(){
 const root=document.documentElement,rootStyle=getComputedStyle(root),bodyStyle=getComputedStyle(document.body)
 const transparent=(color:string)=>color==='transparent'||color==='rgba(0, 0, 0, 0)'
 const headings=['.page-heading .eyebrow','.page-heading h1','.page-heading p'].map(selector=>{const element=document.querySelector(selector);if(!element)return{selector,missing:true};const style=getComputedStyle(element),ancestors:Array<{tag:string;selector:string;color:string;backgroundColor:string;backgroundImage:string}>=[];for(let node:Element|null=element;node&&ancestors.length<8;node=node.parentElement){const parentStyle=getComputedStyle(node);ancestors.push({tag:node.tagName,selector:node.id?`#${node.id}`:typeof node.className==='string'?node.className.split(/\s+/).filter(Boolean).map(name=>`.${name}`).join(''):'',color:parentStyle.color,backgroundColor:parentStyle.backgroundColor,backgroundImage:parentStyle.backgroundImage})}return{selector,color:style.color,backgroundColor:style.backgroundColor,fontSize:style.fontSize,fontWeight:style.fontWeight,nearestOpaqueAncestor:ancestors.find(node=>!transparent(node.backgroundColor))??{source:'canvas'},ancestors}})
 const stylesheets=[...document.styleSheets].map(sheet=>{let ruleCount=0,highContrastRule=false;try{const rules=[...sheet.cssRules];ruleCount=rules.length;highContrastRule=rules.some(rule=>rule.cssText.includes('data-contrast'))}catch{}return{path:sheet.href?new URL(sheet.href).pathname:null,disabled:sheet.disabled,ruleCount,highContrastRule}})
 return{url:location.pathname,attributes:{theme:root.dataset.theme??null,mode:root.dataset.mode??null,contrast:root.dataset.contrast??null},media:{prefersDark:matchMedia('(prefers-color-scheme: dark)').matches,prefersLight:matchMedia('(prefers-color-scheme: light)').matches,prefersReducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches},html:{color:rootStyle.color,backgroundColor:rootStyle.backgroundColor,backgroundImage:rootStyle.backgroundImage,semantic:Object.fromEntries(['--surface-page','--surface-sidebar','--surface-panel','--text-primary','--text-secondary','--text-muted','--accent','--danger','--warning','--success','--focus'].map(name=>[name,rootStyle.getPropertyValue(name).trim()]))},body:{color:bodyStyle.color,backgroundColor:bodyStyle.backgroundColor,backgroundImage:bodyStyle.backgroundImage},effectiveCanvasBackground:!transparent(bodyStyle.backgroundColor)?bodyStyle.backgroundColor:(!transparent(rootStyle.backgroundColor)?rootStyle.backgroundColor:'browser-default'),headings,stylesheets}
}

async function waitForHighContrastPaint(page:Page,scheme:Scheme){
 await page.waitForFunction(expected=>{
  const root=document.documentElement,heading=document.querySelector('.page-heading h1')
  if(root.dataset.theme!=='operations'||root.dataset.mode!==expected||root.dataset.contrast!=='high'||!heading)return false
  const rootStyle=getComputedStyle(root)
  return rootStyle.getPropertyValue('--surface-page').trim()==='#000'&&rootStyle.getPropertyValue('--text-primary').trim()==='#fff'&&getComputedStyle(document.body).backgroundColor==='rgb(0, 0, 0)'&&getComputedStyle(heading).color==='rgb(255, 255, 255)'
 },scheme,{timeout:10000})
}

async function savedHighContrastState(browser:Browser,base:string,scheme:Scheme){
 const context=await browser.newContext({colorScheme:scheme,reducedMotion:'reduce',viewport:{width:1280,height:900}})
 try{
  const page=await context.newPage()
  await page.goto(base)
  await page.getByRole('heading',{name:'Work items',exact:true}).waitFor({state:'visible'})
  await page.locator('#desktop-appearance').selectOption('system')
  await page.locator('#desktop-theme').selectOption('operations')
  await page.locator('#desktop-contrast').selectOption('high')
  await waitForHighContrastPaint(page,scheme)
  return await context.storageState()
 }finally{await context.close()}
}

async function captureAxe(page:Page,label:string,evidence:Evidence,screenshots:Screenshot[]){
 const before=await page.evaluate(readThemePaint)
 const result=await new AxeBuilder({page}).withTags(tags).analyze()
 const after=await page.evaluate(readThemePaint)
 const serious=result.violations.filter(violation=>violation.impact==='serious'||violation.impact==='critical')
 const compact=serious.map(violation=>({id:violation.id,impact:violation.impact,nodes:violation.nodes.map(node=>({target:node.target,checks:node.any.map(check=>{const data=check.data as Record<string,unknown>|undefined;return{id:check.id,message:check.message,foreground:data?.fgColor,background:data?.bgColor,contrastRatio:data?.contrastRatio,expectedContrastRatio:data?.expectedContrastRatio}})}))}))
 evidence.axe_cases.push({label,before,after,serious_or_critical:compact,other_violation_ids:result.violations.filter(violation=>violation.impact!=='serious'&&violation.impact!=='critical').map(violation=>violation.id)})
 screenshots.push({name:`${label}-after-axe.png`,body:await page.screenshot()})
}

async function attachEvidence(info:TestInfo,evidence:Evidence,screenshots:Screenshot[]){
 try{await info.attach('theme-readiness.json',{body:Buffer.from(JSON.stringify(evidence,null,2)),contentType:'application/json'})}catch{}
 for(const screenshot of screenshots)try{await info.attach(screenshot.name,{body:screenshot.body,contentType:'image/png'})}catch{}
}

for(const scheme of ['light','dark'] as const)for(const repeat of [1,2,3])test(`System high contrast initializes before axe: ${scheme} system preference, fresh context ${repeat}`,async({browser},info)=>{
 info.setTimeout(120000)
 const base=process.env.BASE_E2E_BASE??'http://127.0.0.1:4183'
 const evidence:Evidence={source:{source_commit:process.env.UIQA_SOURCE_COMMIT,source_digest:process.env.UIQA_SOURCE_DIGEST,candidate_tree:process.env.UIQA_CANDIDATE_TREE,candidate_version:process.env.UIQA_CANDIDATE_VERSION},browser:`Chromium ${browser.version()}`,system_preference:scheme,reduced_motion:'reduce',appearance:'system',theme:'operations',contrast:'high',route_observations:[],axe_cases:[]}
 const screenshots:Screenshot[]=[]
 let context:BrowserContext|undefined,error:unknown
 try{
  const storageState=await savedHighContrastState(browser,base,scheme)
  context=await browser.newContext({colorScheme:scheme,reducedMotion:'reduce',viewport:{width:1280,height:900},storageState})
  const page=await context.newPage()
  await page.goto(`${base}/system`)
  await page.getByRole('heading',{name:'System workspace',exact:true}).waitFor({state:'visible'})
  evidence.route_observations.push({kind:'direct-load-before-ready',state:await page.evaluate(readThemePaint)})
  screenshots.push({name:'direct-load-before-ready.png',body:await page.screenshot()})
  await waitForHighContrastPaint(page,scheme)
  await captureAxe(page,'direct-load-system',evidence,screenshots)

  await page.goto(`${base}/work-items`)
  await page.getByRole('heading',{name:'Work items',exact:true}).waitFor({state:'visible'})
  await waitForHighContrastPaint(page,scheme)
  await page.getByRole('link',{name:'System',exact:true}).click()
  await page.getByRole('heading',{name:'System workspace',exact:true}).waitFor({state:'visible'})
  await waitForHighContrastPaint(page,scheme)
  evidence.route_observations.push({kind:'client-navigation',route:'/system',state:await page.evaluate(readThemePaint)})
  await captureAxe(page,'client-navigation-system',evidence,screenshots)

  await page.reload()
  await page.getByRole('heading',{name:'System workspace',exact:true}).waitFor({state:'visible'})
  await waitForHighContrastPaint(page,scheme)
  evidence.route_observations.push({kind:'reload',route:'/system',state:await page.evaluate(readThemePaint)})
  await captureAxe(page,'reload-system',evidence,screenshots)
 }catch(caught){error=caught;evidence.error=caught instanceof Error?`${caught.message}\n${caught.stack??''}`:String(caught)}finally{
  if(context)try{await context.close()}catch{}
  await attachEvidence(info,evidence,screenshots)
 }
 if(error)throw error
 expect(evidence.axe_cases.flatMap(testCase=>testCase.serious_or_critical),JSON.stringify(evidence.axe_cases.map(testCase=>({label:testCase.label,violations:testCase.serious_or_critical})),null,2)).toEqual([])
})

test('axe negative control detects white text on the light System canvas',async({browser},info)=>{
 info.setTimeout(60000)
 const scheme='light' as const,base=process.env.BASE_E2E_BASE??'http://127.0.0.1:4183'
 const evidence:Evidence={source:{source_commit:process.env.UIQA_SOURCE_COMMIT,source_digest:process.env.UIQA_SOURCE_DIGEST,candidate_tree:process.env.UIQA_CANDIDATE_TREE,candidate_version:process.env.UIQA_CANDIDATE_VERSION},browser:`Chromium ${browser.version()}`,system_preference:scheme,reduced_motion:'reduce',appearance:'system',theme:'operations',contrast:'high',route_observations:[],axe_cases:[]}
 const screenshots:Screenshot[]=[]
 let context:BrowserContext|undefined,error:unknown
 let negative:{before:unknown;after:unknown;violation:{impact?:string;nodes:Array<{target:string[];checks:Array<{foreground?:unknown;background?:unknown;contrastRatio?:unknown}>}>}|null}|undefined
 try{
  const storageState=await savedHighContrastState(browser,base,scheme)
  context=await browser.newContext({colorScheme:scheme,reducedMotion:'reduce',viewport:{width:1280,height:900},storageState})
  const page=await context.newPage()
  await page.goto(`${base}/system`)
  await page.getByRole('heading',{name:'System workspace',exact:true}).waitFor({state:'visible'})
  await waitForHighContrastPaint(page,scheme)
  await page.evaluate(()=>{document.body.style.backgroundColor='#f4f6f9';document.querySelectorAll('.page-heading .eyebrow,.page-heading h1,.page-heading p').forEach(element=>{(element as HTMLElement).style.color='#ffffff'})})
  await page.waitForFunction(()=>getComputedStyle(document.body).backgroundColor==='rgb(244, 246, 249)'&&getComputedStyle(document.querySelector('.page-heading h1')!).color==='rgb(255, 255, 255)')
  evidence.route_observations.push({kind:'negative-control-induced-failure',route:'/system',state:await page.evaluate(readThemePaint)})
  const before=await page.evaluate(readThemePaint)
  const result=await new AxeBuilder({page}).withTags(tags).analyze()
  const after=await page.evaluate(readThemePaint)
  const contrast=result.violations.find(violation=>violation.id==='color-contrast')
  negative={before,after,violation:contrast?{id:contrast.id,impact:contrast.impact,nodes:contrast.nodes.map(node=>({target:node.target,checks:node.any.map(check=>{const data=check.data as Record<string,unknown>|undefined;return{id:check.id,message:check.message,foreground:data?.fgColor,background:data?.bgColor,contrastRatio:data?.contrastRatio,expectedContrastRatio:data?.expectedContrastRatio}})}))}:null}
  evidence.axe_cases.push({label:'negative-control-white-on-light',before,after,serious_or_critical:negative.violation?.impact==='serious'?[negative.violation]:[],other_violation_ids:result.violations.map(violation=>violation.id)})
  screenshots.push({name:'negative-control-after-axe.png',body:await page.screenshot()})
  await page.evaluate(()=>{document.body.style.removeProperty('background-color');document.querySelectorAll('.page-heading .eyebrow,.page-heading h1,.page-heading p').forEach(element=>(element as HTMLElement).style.removeProperty('color'))})
 }catch(caught){error=caught;evidence.error=caught instanceof Error?`${caught.message}\n${caught.stack??''}`:String(caught)}finally{
  if(context)try{await context.close()}catch{}
  await attachEvidence(info,{...evidence,negative_control:negative},screenshots)
 }
 if(error)throw error
 expect(negative?.violation?.impact).toBe('serious')
 expect(negative?.violation?.nodes.some(node=>node.target.includes('h1')&&node.checks.some(check=>check.foreground==='#ffffff'&&check.background==='#f4f6f9'&&check.contrastRatio===1.08))).toBe(true)
})

test('supported themes preserve semantic accent and status colors in both modes',async({page},info)=>{
 const expected={operations:{light:'#175496',dark:'#91c3ff'},clarity:{light:'#164e94',dark:'#7eb8ff'},minimal:{light:'#315827',dark:'#a5d29b'}} as const
 const status={light:{danger:'#a32235',warning:'#9a5e08',success:'#216646'},dark:{danger:'#ffaaa9',warning:'#f3c878',success:'#91ddb7'}} as const
 const observed:Array<{theme:string;mode:string;tokens:Record<string,string>}>=[]
 try{
  await page.goto('/')
  await page.getByRole('heading',{name:'Work items',exact:true}).waitFor({state:'visible'})
  for(const theme of ['operations','clarity','minimal'] as const)for(const mode of ['light','dark'] as const){
   await page.locator('#desktop-theme').selectOption(theme)
   await page.locator('#desktop-appearance').selectOption(mode)
   await page.waitForFunction(({theme,mode})=>document.documentElement.dataset.theme===theme&&document.documentElement.dataset.mode===mode,{theme,mode})
   const tokens=await page.evaluate(()=>{const style=getComputedStyle(document.documentElement);return Object.fromEntries(['--accent','--danger','--warning','--success'].map(name=>[name,style.getPropertyValue(name).trim()])) as Record<string,string>})
   observed.push({theme,mode,tokens})
   expect(tokens,`${theme} ${mode} semantic color tokens`).toEqual({
    '--accent':expected[theme][mode],
    '--danger':status[mode].danger,
    '--warning':status[mode].warning,
    '--success':status[mode].success,
   })
  }
 }finally{
  await info.attach('semantic-theme-color-matrix.json',{body:Buffer.from(JSON.stringify({source:{source_commit:process.env.UIQA_SOURCE_COMMIT,source_digest:process.env.UIQA_SOURCE_DIGEST,candidate_tree:process.env.UIQA_CANDIDATE_TREE,candidate_version:process.env.UIQA_CANDIDATE_VERSION},browser:`Chromium ${page.context().browser()?.version()}`,matrix:observed},null,2)),contentType:'application/json'})
 }
})
