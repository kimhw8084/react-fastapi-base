import test from 'node:test'
import {request as httpRequest} from 'node:http'
import assert from 'node:assert/strict'
import {mkdtemp,writeFile,mkdir,rm,symlink} from 'node:fs/promises'
import {tmpdir} from 'node:os'
import {join} from 'node:path'
import {createStaticServer,validateRuntime} from '../server.mjs'
const runtime={schemaVersion:1,apiBase:'',defaultTheme:'operations',titleOverride:''}
async function fixture(fn){
 const parent=await mkdtemp(join(tmpdir(),'golden-static-test-'));const root=join(parent,'dist');await mkdir(root)
 await writeFile(join(root,'index.html'),'<!doctype html><h1>Static test fixture, not the React application</h1>')
 await writeFile(join(root,'runtime-config.json'),JSON.stringify(runtime))
 await mkdir(join(root,'assets'));await writeFile(join(root,'assets','app-AbCd123456.js'),'export const fixture=true')
 const server=await createStaticServer({root});await new Promise(r=>server.listen(0,'127.0.0.1',r))
 const base=`http://127.0.0.1:${server.address().port}`
 try{await fn({base,root,parent})}finally{await new Promise(r=>server.close(r));await rm(parent,{recursive:true,force:true})}
}
test('static HTML has CSP and no-store',()=>fixture(async({base})=>{const r=await fetch(base+'/',{headers:{Accept:'text/html'}});assert.equal(r.status,200);assert.match(r.headers.get('content-security-policy'),/script-src 'self'/);assert.equal(r.headers.get('cache-control'),'no-store')}))
test('SPA navigation works but API is never HTML fallback',()=>fixture(async({base})=>{assert.equal((await fetch(base+'/work-items',{headers:{Accept:'text/html'}})).status,200);assert.equal((await fetch(base+'/api/v1/bootstrap',{headers:{Accept:'text/html'}})).status,404)}))
test('hashed assets are immutable; missing asset is 404',()=>fixture(async({base})=>{const r=await fetch(base+'/assets/app-AbCd123456.js');assert.match(r.headers.get('cache-control'),/immutable/);assert.equal((await fetch(base+'/assets/nope.js')).status,404)}))
test('invalid host and unsafe method fail',()=>fixture(async({base})=>{const status=await new Promise((resolve,reject)=>{const r=httpRequest(base+'/',{headers:{Host:'attacker.test'}},response=>{response.resume();resolve(response.statusCode)});r.on('error',reject);r.end()});assert.equal(status,400);assert.equal((await fetch(base+'/',{method:'POST'})).status,405)}))
test('symlink cannot disclose source outside dist',()=>fixture(async({base,root,parent})=>{await writeFile(join(parent,'private.json'),'secret');await symlink(join(parent,'private.json'),join(root,'leak.json'));assert.equal((await fetch(base+'/leak.json')).status,404)}))
test('runtime config can change without rebuilding; corrupt config fails closed',()=>fixture(async({base,root})=>{await writeFile(join(root,'runtime-config.json'),JSON.stringify({...runtime,titleOverride:'Updated'}));assert.equal((await(await fetch(base+'/runtime-config.json')).json()).titleOverride,'Updated');await writeFile(join(root,'runtime-config.json'),'broken');assert.equal((await fetch(base+'/runtime-config.json')).status,503)}))
test('hidden files and source maps are not served',()=>fixture(async({base,root})=>{await writeFile(join(root,'x.map'),'source');assert.equal((await fetch(base+'/x.map')).status,404);assert.equal((await fetch(base+'/.env')).status,400)}))
test('runtime rejects credentials, scripts, unknown keys and bad version',()=>{for(const patch of [{apiBase:'javascript:alert(1)'},{apiBase:'https://user:pass@api.test'},{secret:'x'},{schemaVersion:2}])assert.throws(()=>validateRuntime({...runtime,...patch}))})

test('embedded lab has a same-origin frame boundary; app remains non-frameable',()=>fixture(async({base,root})=>{
 await mkdir(join(root,'experience-lab'));await writeFile(join(root,'experience-lab','index.html'),'<!doctype html><h1>Lab fixture</h1>')
 const parent=await fetch(base+'/lab',{headers:{Accept:'text/html'}}),child=await fetch(base+'/experience-lab/index.html')
 assert.equal(parent.status,200);assert.equal(child.status,200)
 assert.match(parent.headers.get('content-security-policy'),/frame-src 'self'/)
 assert.match(parent.headers.get('content-security-policy'),/frame-ancestors 'none'/)
 assert.match(child.headers.get('content-security-policy'),/frame-ancestors 'self'/)
 assert.doesNotMatch(child.headers.get('content-security-policy'),/script-src [^;]*unsafe-inline/)
}))
