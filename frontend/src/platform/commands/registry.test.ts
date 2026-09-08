import { describe, expect, it, vi } from 'vitest'
import { ActionRegistry, type RegisteredAction } from './registry'

const context={entity:'work_items',permissions:['read','write'],selectionCount:1,mode:'table'} as const
function action(id:string,placements:RegisteredAction['placements']):RegisteredAction{return {id,label:id,entity:'work_items',placements,run:vi.fn()}}

describe('universal action registry',()=>{
 it('resolves the same action for every declared surface',()=>{
  const edit=action('edit', ['toolbar','context','keyboard','palette','selection','dossier','inspector'])
  const registry=new ActionRegistry([edit])
  for(const placement of edit.placements) expect(registry.all(context,placement).map(item=>item.id)).toEqual(['edit'])
 })
 it('enforces entity, permission and selection policy before execution',async()=>{
  const edit=action('edit',['toolbar']);const registry=new ActionRegistry([edit])
  await expect(registry.execute('edit',context)).resolves.toBeUndefined()
  expect(edit.run).toHaveBeenCalledTimes(1)
  await expect(registry.execute('edit',{...context,entity:'projects'})).rejects.toThrow('Action unavailable')
 })
 it('rejects duplicate registrations',()=>{const registry=new ActionRegistry([action('edit',['toolbar'])]);expect(()=>registry.register(action('edit',['context']))).toThrow('Duplicate action')})
})
