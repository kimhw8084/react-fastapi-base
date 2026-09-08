import {describe,it,expect} from 'vitest'
import {readStorage,storageKey,writeStorage} from './storage'
describe('scoped preferences',()=>{
 it('separates users and tenants',()=>{expect(storageKey('a','alice','t','view')).not.toBe(storageKey('a','bob','t','view'));expect(storageKey('a','alice','t','view')).not.toBe(storageKey('a','alice','t2','view'))})
 it('restores a validated value',()=>{localStorage.clear();writeStorage('x',{size:10});expect(readStorage('x',{size:0},v=>v as {size:number})).toEqual({size:10})})
 it('rejects corrupt serialized data without crashing',()=>{localStorage.setItem('x','{bad');expect(readStorage('x',3,Number)).toBe(3)})
})
