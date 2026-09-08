import { describe,expect,it } from 'vitest'
import { alignNodes,boundedHistory,distributeNodes,nodesInRect,reconnectEdge } from './diagramModel'
describe('diagram editing primitives',()=>{
 const nodes=[{id:'a',x:20,y:80},{id:'b',x:100,y:20},{id:'c',x:180,y:140}]
 it('selects nodes in a normalized rectangle',()=>expect(nodesInRect(nodes,{left:190,top:150,right:0,bottom:0})).toEqual(['a','b','c']))
 it('aligns and distributes without mutating input',()=>{expect(alignNodes(nodes,['a','b'],'y').map(node=>node.y)).toEqual([20,20,140]);expect(distributeNodes(nodes,['a','b','c'],'x').map(node=>node.x)).toEqual([20,100,180]);expect(nodes[0]!.y).toBe(80)})
 it('reconnects one endpoint and preserves other edges',()=>expect(reconnectEdge([{id:'e1',source:'a',target:'b'},{id:'e2',source:'b',target:'c'}],'e1','target','c')).toEqual([{id:'e1',source:'a',target:'c'},{id:'e2',source:'b',target:'c'}]))
 it('bounds undo history',()=>expect(boundedHistory([1,2],3,2)).toEqual([2,3]))
})
