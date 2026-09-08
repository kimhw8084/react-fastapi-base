export type CommandPlacement = 'toolbar'|'context'|'keyboard'|'palette'|'selection'|'dossier'|'inspector'
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
  shortcut?:string
  description?:string
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

export interface RegisteredAction extends CommandDefinition {
  run:(context:CommandContext)=>void|Promise<void>
}

/** One business action registry shared by every presentation surface. */
export class ActionRegistry {
  private readonly actions = new Map<string, RegisteredAction>()

  constructor(actions:readonly RegisteredAction[] = []) { actions.forEach(action=>this.register(action)) }

  register(action:RegisteredAction):void {
    if(this.actions.has(action.id)) throw new Error(`Duplicate action: ${action.id}`)
    this.actions.set(action.id,action)
  }

  get(id:string):RegisteredAction|undefined { return this.actions.get(id) }

  all(context:CommandContext,placement?:CommandPlacement):RegisteredAction[] {
    const values=[...this.actions.values()]
    return placement ? values.filter(action=>action.placements.includes(placement)&&commandAvailable(action,context)) : values.filter(action=>commandAvailable(action,context))
  }

  async execute(id:string,context:CommandContext):Promise<void> {
    const action=this.actions.get(id)
    if(!action||!commandAvailable(action,context)) throw new Error(`Action unavailable: ${id}`)
    await action.run(context)
  }
}

export function actionToPaletteCommand(action:RegisteredAction,context:CommandContext){
  return {id:action.id,label:action.label,description:action.description,keywords:[action.entity??'',action.id],shortcut:action.shortcut,action:()=>{void action.run(context)}}
}
