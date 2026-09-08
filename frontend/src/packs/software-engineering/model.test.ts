import { describe,expect,it } from 'vitest'
import { artifactRollbackContext,correlateLogs,traceSummary } from './model'
describe('software engineering projection parity',()=>{
 const rows=[{span_id:'s1',trace_id:'t1',timestamp:100,duration_ms:10,severity:'info'},{span_id:'s2',trace_id:'t1',timestamp:108,duration_ms:20,severity:'error'}]
 it('correlates logs and summarizes traces',()=>{expect(correlateLogs(rows,'t1')).toEqual(rows);expect(traceSummary(rows)).toEqual({spanCount:2,start:100,end:128,durationMs:28,errorCount:1})})
 it('preserves rollback context without exposing secrets',()=>expect(artifactRollbackContext({ids:['a1']},{revision:'r2',previous_revision:'r1',environment:'staging'})).toEqual({artifactIds:['a1'],currentRevision:'r2',previousRevision:'r1',rollbackAvailable:true,environment:'staging'}))
})
