export interface DiagramNodePosition { id:string; x:number; y:number }
export interface DiagramEdgeEndpoints { id:string; source:string; target:string }
export interface DiagramRect { left:number; top:number; right:number; bottom:number }

export function nodesInRect<T extends DiagramNodePosition>(nodes:T[],rect:DiagramRect):string[]{
 const left=Math.min(rect.left,rect.right),right=Math.max(rect.left,rect.right),top=Math.min(rect.top,rect.bottom),bottom=Math.max(rect.top,rect.bottom)
 return nodes.filter(node=>node.x>=left&&node.x<=right&&node.y>=top&&node.y<=bottom).map(node=>node.id)
}
export function alignNodes<T extends DiagramNodePosition>(nodes:T[],ids:string[],axis:'x'|'y'):T[]{
 const selected=nodes.filter(node=>ids.includes(node.id));if(selected.length<2)return nodes
 const target=axis==='x'?Math.min(...selected.map(node=>node.x)):Math.min(...selected.map(node=>node.y)),chosen=new Set(ids)
 return nodes.map(node=>chosen.has(node.id)?{...node,[axis]:target}:node)
}
export function distributeNodes<T extends DiagramNodePosition>(nodes:T[],ids:string[],axis:'x'|'y'):T[]{
 const selected=nodes.filter(node=>ids.includes(node.id)).sort((left,right)=>left[axis]-right[axis]);if(selected.length<3)return nodes
 const first=selected[0]![axis],last=selected[selected.length-1]![axis],step=(last-first)/(selected.length-1),positions=new Map(selected.map((node,index)=>[node.id,first+step*index]))
 return nodes.map(node=>positions.has(node.id)?{...node,[axis]:positions.get(node.id)!}:node)
}
export function reconnectEdge<T extends DiagramEdgeEndpoints>(edges:T[],edgeId:string,endpoint:'source'|'target',nodeId:string):T[]{return edges.map(edge=>edge.id===edgeId?{...edge,[endpoint]:nodeId}:edge)}
export function boundedHistory<T>(history:T[],snapshot:T,max=50):T[]{return [...history,snapshot].slice(-Math.max(1,max))}
