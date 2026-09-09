export function requiredStringDraft(value:string,label:string):string{
 const normalized=value.trim();if(!normalized)throw new Error(`${label} is required.`);return normalized
}
export function nullableStringDraft(value:string):string|null{const normalized=value.trim();return normalized||null}
export function parseIntegerDraft(value:string,label:string):number{
 if(value.trim()==='')throw new Error(`${label} is required.`)
 const parsed=Number(value)
 if(!Number.isSafeInteger(parsed))throw new Error(`${label} must be a whole number.`)
 return parsed
}
export function parseNumberDraft(value:string,label:string):number{
 if(value.trim()==='')throw new Error(`${label} is required.`)
 const parsed=Number(value)
 if(!Number.isFinite(parsed))throw new Error(`${label} must be a valid number.`)
 return parsed
}
export function parseBooleanDraft(value:string):boolean{
 if(value==='true')return true
 if(value==='false')return false
 throw new Error('Boolean value must be true or false.')
}
export function parseEnumDraft<const T extends readonly string[]>(value:string,label:string,choices:T):T[number]
export function parseEnumDraft<const T extends readonly string[]>(value:string,label:string,choices:T,fallback:T[number]):T[number]
export function parseEnumDraft<const T extends readonly string[]>(value:string,label:string,choices:T,fallback:null):T[number]|null
export function parseEnumDraft<const T extends readonly string[]>(value:string,label:string,choices:T,fallback:undefined):T[number]|undefined
export function parseEnumDraft<const T extends readonly string[]>(value:string,label:string,choices:T,fallback?:T[number]|null):T[number]|null|undefined{
 const normalized=value.trim()
 if(!normalized)return fallback
 if(!choices.includes(normalized as T[number]))throw new Error(`Choose a valid ${label.toLowerCase()}.`)
 return normalized as T[number]
}
export function datetimeToInput(value:unknown):string{
 if(value==null||value==='')return ''
 const date=new Date(String(value));if(Number.isNaN(date.getTime()))return ''
 const local=new Date(date.getTime()-date.getTimezoneOffset()*60000)
 return local.toISOString().slice(0,16)
}
export function datetimeInputToIso(value:string,label:string):string{
 if(!value.trim())throw new Error(`${label} is required.`)
 const date=new Date(value);if(Number.isNaN(date.getTime()))throw new Error(`${label} must be a valid date and time.`)
 return date.toISOString()
}

export function parseJsonObjectDraft(value:string,label:string):Record<string,unknown>{
 let parsed:unknown
 try{parsed=JSON.parse(value)}catch{throw new Error(`${label} must contain valid JSON.`)}
 if(parsed===null||Array.isArray(parsed)||typeof parsed!=='object')throw new Error(`${label} must be a JSON object.`)
 return parsed as Record<string,unknown>
}
export function readJsonDraft(value:unknown):string{
 if(value==null)return ''
 if(typeof value==='string'){
  try{return JSON.stringify(parseJsonObjectDraft(value,'JSON'),null,2)}catch{return value}
 }
 return JSON.stringify(value,null,2)
}
export function parseJsonArrayDraft(value:string,label:string):unknown[]{
 let parsed:unknown
 try{parsed=JSON.parse(value)}catch{throw new Error(`${label} must contain valid JSON.`)}
 if(!Array.isArray(parsed))throw new Error(`${label} must be a JSON array.`)
 return parsed
}
export function readJsonArrayDraft(value:unknown):string{
 if(value==null)return ''
 if(typeof value==='string'){
  try{return JSON.stringify(parseJsonArrayDraft(value,'JSON'),null,2)}catch{return value}
 }
 return JSON.stringify(Array.isArray(value)?value:[],null,2)
}
export function parseMultiSelectDraft<const T extends readonly string[]>(value:string,label:string,choices:T,required=false):T[number][]{
 let parsed:unknown
 try{parsed=JSON.parse(value)}catch{throw new Error(`${label} selection is invalid.`)}
 if(!Array.isArray(parsed)||parsed.some(item=>typeof item!=='string'))throw new Error(`${label} selection is invalid.`)
 const items=parsed as string[]
 if(required&&items.length===0)throw new Error(`${label} requires at least one choice.`)
 if(new Set(items).size!==items.length)throw new Error(`${label} contains duplicate choices.`)
 if(items.some(item=>!choices.includes(item)))throw new Error(`${label} contains an unsupported choice.`)
 return items as T[number][]
}
export function readMultiSelectDraft(value:unknown):string{
 if(value==null)return ''
 const items=Array.isArray(value)?value:[]
 return JSON.stringify(items)
}

import type { FieldDefinition } from '../../generated/schema'
export function parseWorkspaceFieldDraft(field:FieldDefinition,value:string):unknown{
 if(field.read_only)throw new Error(`${field.label} is read only.`)
 const raw=value??''
 if(raw.trim()===''&&field.nullable)return null
 if(field.kind==='select'){
  const selected=raw.trim();if(field.required&&!selected)throw new Error(`${field.label} is required.`)
  if(selected&&!field.choices.includes(selected))throw new Error(`Choose a valid ${field.label.toLowerCase()}.`)
  return selected
 }
 if(field.kind==='multiselect'||field.kind==='multi_enum')return parseMultiSelectDraft(raw,field.label,field.choices,field.required)
 if(field.kind==='boolean')return parseBooleanDraft(raw)
 if(field.kind==='integer')return parseIntegerDraft(raw,field.label)
 if(['number','decimal','percent','duration','scientific','unit_number','range','tolerance'].includes(field.kind)){
  const parsed=parseNumberDraft(raw,field.label)
  if(field.minimum!=null&&parsed<field.minimum)throw new Error(`${field.label} must be at least ${field.minimum}.`)
  if(field.maximum!=null&&parsed>field.maximum)throw new Error(`${field.label} must be at most ${field.maximum}.`)
  return parsed
 }
 if(field.kind==='datetime')return datetimeInputToIso(raw,field.label)
 if(field.kind==='json'||field.kind==='object'||field.kind==='coordinates')return parseJsonObjectDraft(raw,field.label)
 if(field.kind==='array')return parseJsonArrayDraft(raw,field.label)
 if(field.required)return requiredStringDraft(raw,field.label)
 return raw.trim()
}
