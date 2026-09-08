export interface PlanningTaskNode { id:string; duration:number }
export interface PlanningDependency { source:string; target:string }
export function criticalPath(tasks:readonly PlanningTaskNode[],dependencies:readonly PlanningDependency[]):string[]{
 const durations=new Map(tasks.map(task=>[task.id,Math.max(1,Number(task.duration)||1)]))
 const prereqs=new Map<string,string[]>()
 for(const edge of dependencies){if(!durations.has(edge.source)||!durations.has(edge.target))continue;(prereqs.get(edge.source)??(prereqs.set(edge.source,[]),prereqs.get(edge.source)!)).push(edge.target)}
 const memo=new Map<string,{score:number,path:string[]}>();const visiting=new Set<string>()
 const solve=(id:string):{score:number;path:string[]}=>{const cached=memo.get(id);if(cached)return cached;if(visiting.has(id))return{score:-Infinity,path:[]};visiting.add(id);let best={score:0,path:[] as string[]};for(const dep of prereqs.get(id)??[]){const candidate=solve(dep);if(candidate.score>best.score)best=candidate}visiting.delete(id);const result={score:best.score+(durations.get(id)??1),path:[...best.path,id]};memo.set(id,result);return result}
 let best={score:-Infinity,path:[] as string[]};for(const task of tasks){const candidate=solve(task.id);if(candidate.score>best.score)best=candidate}return best.path
}
export function shiftIsoDate(value:string,days:number):string{const date=new Date(`${value}T00:00:00Z`);if(Number.isNaN(date.getTime()))throw new Error('Invalid ISO date.');date.setUTCDate(date.getUTCDate()+days);return date.toISOString().slice(0,10)}
