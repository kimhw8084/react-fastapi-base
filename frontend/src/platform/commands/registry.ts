export type CommandPlacement = 'toolbar'|'context'|'palette'|'selection'|'inspector'
export interface CommandDefinition {
  id:string
  label:string
  entity?:string
  permission?:string
  requiresSelection?:boolean
  minSelection?:number
  maxSelection?:number
  modes?:string[]
  placements:CommandPlacement[]
  destructive?:boolean
}
export interface CommandContext {
  entity:string
  permissions:readonly string[]
  selectionCount:number
  mode?:string
  readOnly?:boolean
}
export function commandAvailable(command:CommandDefinition,context:CommandContext):boolean{
  if(command.entity&&command.entity!==context.entity)return false
  if(command.permission&&!context.permissions.includes(command.permission))return false
  if(context.readOnly&&command.permission&&command.permission!=='read')return false
  if(command.requiresSelection&&context.selectionCount===0)return false
  if(command.minSelection!==undefined&&context.selectionCount<command.minSelection)return false
  if(command.maxSelection!==undefined&&context.selectionCount>command.maxSelection)return false
  if(command.modes?.length&&(!context.mode||!command.modes.includes(context.mode)))return false
  return true
}
export function resolveCommands(commands:readonly CommandDefinition[],context:CommandContext,placement:CommandPlacement):CommandDefinition[]{
  return commands.filter(command=>command.placements.includes(placement)&&commandAvailable(command,context))
}
