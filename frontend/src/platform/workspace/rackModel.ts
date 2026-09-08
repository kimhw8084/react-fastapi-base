export interface RackConnectionEdge { id:string; source:string; target:string }
export interface RackTrace { nodes:string[]; edges:string[] }
export function traceRackConnections(edges:readonly RackConnectionEdge[],start:string,end:string):RackTrace{
 if(!start||!end)return{nodes:[],edges:[]};if(start===end)return{nodes:[start],edges:[]}
 const adjacency=new Map<string,Array<{next:string;edge:string}>>()
 for(const edge of edges){(adjacency.get(edge.source)??(adjacency.set(edge.source,[]),adjacency.get(edge.source)!)).push({next:edge.target,edge:edge.id});(adjacency.get(edge.target)??(adjacency.set(edge.target,[]),adjacency.get(edge.target)!)).push({next:edge.source,edge:edge.id})}
 const queue=[start];const seen=new Set([start]);const previous=new Map<string,{node:string;edge:string}>()
 while(queue.length){const current=queue.shift()!;for(const item of adjacency.get(current)??[]){if(seen.has(item.next))continue;seen.add(item.next);previous.set(item.next,{node:current,edge:item.edge});if(item.next===end){const nodes=[end],pathEdges:string[]=[];let cursor=end;while(cursor!==start){const prior=previous.get(cursor);if(!prior)return{nodes:[],edges:[]};pathEdges.unshift(prior.edge);nodes.unshift(prior.node);cursor=prior.node}return{nodes,edges:pathEdges}}queue.push(item.next)}}
 return{nodes:[],edges:[]}
}
