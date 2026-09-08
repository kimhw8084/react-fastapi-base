import { describe,expect,it } from 'vitest'
import { capacityMetrics,equipmentMetrics,routeMetrics,waferDefectSummary } from './model'
describe('semiconductor projection parity',()=>{
 it('summarizes zones and bins',()=>expect(waferDefectSummary([{x:0,y:0,bin:'1'},{x:1,y:1,bin:'2'},{x:2,y:2,bin:'1'}],3,3,['1'],1)).toMatchObject({goodDie:2,defectCount:1,defectsByZone:{edge:0,center:1}}))
 it('reports route, reliability and capacity signals',()=>{expect(routeMetrics([{name:'Etch',status:'done'},{name:'Metrology',status:'hold',queue_minutes:12}],'2026-09-07T12:00:00.000Z',new Date('2026-09-07T14:00:00.000Z'))).toMatchObject({onHold:true,queueMinutes:12,progressPercent:50});expect(equipmentMetrics([{state:'production',duration:90},{state:'unscheduled_down',duration:30}],120)).toMatchObject({mtbfMinutes:90,mttrMinutes:30});expect(capacityMetrics(120,100).bottleneck).toBe(true)})
})
