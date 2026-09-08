import {cp,mkdir,rm} from 'node:fs/promises'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
const frontend=path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const target=path.join(frontend,'public/experience-lab')
// Generated apps may disable the example showroom while retaining widget source.
await rm(target,{recursive:true,force:true})
if(process.env.BASE_INCLUDE_LAB!=='false'){
 await mkdir(target,{recursive:true})
 await cp(path.join(frontend,'../experience-lab/public'),target,{recursive:true})
}
