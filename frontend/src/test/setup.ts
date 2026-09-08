import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
afterEach(cleanup)
// DOM-only component tests do not claim browser focus/geometry verification.
if (!HTMLDialogElement.prototype.showModal) HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
if (!HTMLDialogElement.prototype.close) HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}
try {
  void globalThis.localStorage
} catch {
  Object.defineProperty(globalThis,'localStorage',{configurable:true,value:undefined})
}
if (typeof globalThis.localStorage==='undefined') {
  const values=new Map<string,string>()
  Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{
    get length(){return values.size},
    clear:()=>values.clear(),
    getItem:(key:string)=>values.get(key)??null,
    key:(index:number)=>[...values.keys()][index]??null,
    removeItem:(key:string)=>{values.delete(key)},
    setItem:(key:string,value:string)=>{values.set(key,String(value))},
  } as Storage})
}
