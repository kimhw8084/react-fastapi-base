/** Optional native Node PaaS entrypoint. Static publishers can serve dist/ directly.
 * No reverse proxy, authentication implementation or arbitrary filesystem serving.
 */
import {createServer} from 'node:http'
import {readFile, realpath, stat} from 'node:fs/promises'
import {resolve, relative, extname, isAbsolute} from 'node:path'
import {fileURLToPath} from 'node:url'

const TYPES={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.ico':'image/x-icon','.woff2':'font/woff2'}
export function validateRuntime(value){
  if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Invalid runtime config.')
  const allowed=['schemaVersion','apiBase','defaultTheme','titleOverride']
  if(Object.keys(value).some(k=>!allowed.includes(k))||value.schemaVersion!==1||typeof value.apiBase!=='string'||typeof value.titleOverride!=='string'||value.titleOverride.length>80||!['operations','clarity','minimal'].includes(value.defaultTheme))throw new Error('Invalid runtime config.')
  if(value.apiBase){if(/[;'"\s]/.test(value.apiBase))throw new Error('Invalid origin.');const url=new URL(value.apiBase);if(!['https:','http:'].includes(url.protocol)||url.username||url.password||url.pathname!=='/'||url.search||url.hash||value.apiBase.endsWith('/'))throw new Error('API must be an origin.')}
  return value
}
export async function createStaticServer({root,runtimePath,allowedHosts=['127.0.0.1','localhost'],production=false}){
  root=await realpath(root)
  await stat(resolve(root,'index.html'))
  runtimePath=runtimePath??resolve(root,'runtime-config.json')
  const readRuntime=async()=>{
    const config=validateRuntime(JSON.parse(await readFile(runtimePath,'utf8')))
    if(production&&config.apiBase&&!config.apiBase.startsWith('https://'))throw new Error('Production API must use HTTPS.')
    return config
  }
  await readRuntime()
  if(production&&(!allowedHosts.length||allowedHosts.some(h=>['*','localhost','127.0.0.1'].includes(h))))throw new Error('Explicit production hosts are required.')
  const server=createServer(async(req,res)=>{
    try{
      const host=req.headers.host??''
      if(!host||/[\\/@?#\s]/.test(host)){res.writeHead(400);res.end('Invalid host');return}
      const hostname=new URL(`http://${host}`).hostname
      if(!allowedHosts.includes(hostname)){res.writeHead(400);res.end('Invalid host');return}
      if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});res.end();return}
      const config=await readRuntime()
      const connect=["'self'",...(config.apiBase?[config.apiBase]:[])].join(' ')
      const headers={
        'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cache-Control':'no-store',
        'Permissions-Policy':'camera=(), microphone=(), geolocation=()',
        // AG Grid uses inline style geometry; inline scripts and eval remain forbidden.
        'Content-Security-Policy':`default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src ${connect}; frame-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; object-src 'none'`,
      }
      let rawPath
      try{rawPath=decodeURIComponent((req.url??'/').split('?')[0])}catch{res.writeHead(400,headers);res.end('Invalid path');return}
      if(rawPath.includes('\\')||rawPath.includes('\0')||rawPath.split('/').some(p=>p==='..'||(p.startsWith('.')&&p!==''))){res.writeHead(400,headers);res.end('Invalid path');return}
      // Only the explicitly packaged Lab may be framed by our same-origin host.
      // Application pages remain non-frameable; external embedding is never allowed.
      if(rawPath.startsWith('/experience-lab/')) headers['Content-Security-Policy']=headers['Content-Security-Policy'].replace("frame-ancestors 'none'","frame-ancestors 'self'");
      if(rawPath==='/runtime-config.json'){
        res.writeHead(200,{...headers,'Content-Type':TYPES['.json']});res.end(req.method==='HEAD'?'':JSON.stringify(config));return
      }
      if(rawPath==='/healthz'){
        res.writeHead(200,{...headers,'Content-Type':TYPES['.json']});res.end(req.method==='HEAD'?'':'{"alive":true}');return
      }
      if(rawPath==='/api'||rawPath.startsWith('/api/')){res.writeHead(404,headers);res.end('API is published separately.');return}
      let target=rawPath==='/'?resolve(root,'index.html'):resolve(root,'.'+rawPath)
      let info
      try{info=await stat(target)}catch{}
      if(!info?.isFile()){
        if(extname(rawPath)||!String(req.headers.accept??'').includes('text/html')){res.writeHead(404,headers);res.end('Not found');return}
        target=resolve(root,'index.html')
      }
      target=await realpath(target)
      const child=relative(root,target)
      if(child.startsWith('..')||isAbsolute(child)){res.writeHead(404,headers);res.end('Not found');return}
      const type=TYPES[extname(target)]
      if(!type){res.writeHead(404,headers);res.end('Not found');return}
      const content=await readFile(target)
      const immutable=rawPath.startsWith('/assets/')&&/[-.][A-Za-z0-9_-]{8,}\.[a-z0-9]+$/.test(rawPath)
      res.writeHead(200,{...headers,'Content-Type':type,'Content-Length':content.length,'Cache-Control':immutable?'public, max-age=31536000, immutable':'no-store'})
      res.end(req.method==='HEAD'?undefined:content)
    }catch{
      res.writeHead(503,{'Content-Type':'text/plain; charset=utf-8','Cache-Control':'no-store'});res.end('Static service configuration unavailable.')
    }
  })
  server.requestTimeout=15000;server.headersTimeout=10000;server.keepAliveTimeout=5000
  return server
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const root=resolve(fileURLToPath(new URL('.',import.meta.url)),'dist')
  const allowedHosts=JSON.parse(process.env.BASE_FRONTEND_HOSTS??'["127.0.0.1","localhost"]')
  const server=await createStaticServer({root,runtimePath:process.env.BASE_FRONTEND_RUNTIME_CONFIG,allowedHosts,production:process.env.NODE_ENV==='production'})
  const port=Number(process.env.PORT??4173)
  if(!Number.isInteger(port)||port<1||port>65535)throw new Error('Invalid PORT.')
  server.listen(port,process.env.HOST??'0.0.0.0',()=>console.log(`Static frontend listening on ${port}`))
}
