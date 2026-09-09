export interface PlanningTaskNode { id:string; duration:number }
export interface PlanningDependency { source:string; target:string }
export function criticalPath(tasks:readonly PlanningTaskNode[],dependencies:readonly PlanningDependency[]):string[]{
 const durations=new Map(tasks.map(task=>[task.id,Math.max(1,Number(task.duration)||1)]))
 const next=new Map<string,string[]>()
 // The canonical relationship is "source depends on target".  Build the
 // traversal in schedule order so the returned path reads prerequisite →
 // dependent even though the stored edge is dependent → prerequisite.
 for(const edge of dependencies){if(!durations.has(edge.source)||!durations.has(edge.target))continue;(next.get(edge.target)??(next.set(edge.target,[]),next.get(edge.target)!)).push(edge.source)}
 const memo=new Map<string,{score:number,path:string[]}>();const visiting=new Set<string>()
 const solve=(id:string):{score:number;path:string[]}=>{const cached=memo.get(id);if(cached)return cached;if(visiting.has(id))return{score:-Infinity,path:[]};visiting.add(id);let best={score:-Infinity,path:[] as string[]};for(const child of next.get(id)??[]){const candidate=solve(child);if(candidate.score>best.score)best=candidate}visiting.delete(id);const tail=best.score===-Infinity?{score:0,path:[]}:best;const result={score:tail.score+(durations.get(id)??1),path:[id,...tail.path]};memo.set(id,result);return result}
 let best={score:-Infinity,path:[] as string[]};for(const task of tasks){const candidate=solve(task.id);if(candidate.score>best.score)best=candidate}return best.path
}
export function shiftIsoDate(value:string,days:number):string{const date=new Date(`${value}T00:00:00Z`);if(Number.isNaN(date.getTime()))throw new Error('Invalid ISO date.');date.setUTCDate(date.getUTCDate()+days);return date.toISOString().slice(0,10)}
export function baselineSlipDays(actualEnd:string,baselineEnd:string):number{const actual=Date.parse(`${actualEnd.slice(0,10)}T00:00:00Z`),baseline=Date.parse(`${baselineEnd.slice(0,10)}T00:00:00Z`);if(!actualEnd||!baselineEnd||!Number.isFinite(actual)||!Number.isFinite(baseline))return 0;return Math.max(0,Math.round((actual-baseline)/86400000))}
