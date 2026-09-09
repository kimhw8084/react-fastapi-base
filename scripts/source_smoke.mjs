/** Parse all TypeScript syntax and execute pure client modules, without pretending
 * this substitutes for a dependency-resolved TypeScript or browser build.
 */
import {createRequire} from 'node:module'
import {fileURLToPath} from 'node:url'
import {resolve,dirname,join,relative} from 'node:path'
import {readdir,readFile,mkdir,writeFile,mkdtemp,rm} from 'node:fs/promises'
import {tmpdir} from 'node:os'
import {spawnSync} from 'node:child_process'
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..')
const require=createRequire(join(root,'frontend','package.json'))
let ts
try{ts=require('typescript')}catch{
 const global=spawnSync('npm',['root','-g'],{encoding:'utf8'})
 if(global.status!==0)throw new Error('TypeScript unavailable; source smoke is BLOCKED.')
 ts=require(join(global.stdout.trim(),'typescript'))
}
async function files(dir){return(await Promise.all((await readdir(dir,{withFileTypes:true})).map(e=>e.isDirectory()?files(join(dir,e.name)):[join(dir,e.name)]))).flat()}
const sourceFiles=(await files(join(root,'frontend','src'))).filter(p=>/\.tsx?$/.test(p))
let count=0
for(const path of sourceFiles){const content=await readFile(path,'utf8');const sf=ts.createSourceFile(path,content,ts.ScriptTarget.Latest,true,path.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS);if(sf.parseDiagnostics.length){console.error(sf.parseDiagnostics.map(d=>ts.flattenDiagnosticMessageText(d.messageText,'\n')));process.exit(1)}count++}
console.log(`TypeScript syntax only: ${count} files parsed. This is NOT a full typecheck.`)
const temp=await mkdtemp(join(tmpdir(),'golden-client-smoke-'))
try{
 await writeFile(join(temp,'package.json'),'{"type":"module"}')
 for(const name of ['platform/api/runtime.ts','platform/api/client.ts','platform/state/storage.ts','platform/workspace/fieldDraft.ts','platform/workspace/types.ts','platform/workspace/workspaceState.ts','platform/workspace/query.ts','platform/workspace/dashboardModel.ts','platform/workspace/riskModel.ts','platform/ui/surface.ts','platform/ui/surfaceStack.ts','platform/ui/theme.ts','platform/commands/registry.ts','platform/layout/model.ts','platform/workspace/planningModel.ts','platform/workspace/rackModel.ts','platform/workspace/tableModel.ts','platform/engineering/spcModel.ts','packs/semiconductor/model.ts','packs/software-engineering/model.ts','generated/schema.ts']){
  const source=await readFile(join(root,'frontend/src',name),'utf8')
  let output=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText
  output=output.replace(/(from\s+['"])(\.[^'"]+)(['"])/g,(_,a,b,c)=>a+b+(b.endsWith('.js')?'':'.js')+c)
  const target=join(temp,name.replace(/\.ts$/,'.js'));await mkdir(dirname(target),{recursive:true});await writeFile(target,output)
 }
 const r=spawnSync(process.execPath,['--test',join(root,'frontend/tests/pure-client.test.mjs')],{stdio:'inherit',env:{...process.env,BASE_SMOKE_ROOT:temp}})
 if(r.status!==0)process.exitCode=r.status??1
}finally{await rm(temp,{recursive:true,force:true})}
