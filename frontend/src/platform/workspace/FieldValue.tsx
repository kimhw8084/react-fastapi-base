import type { FieldDefinition } from '../../generated/schema'

function displayNumber(value:unknown,field:FieldDefinition):string{
 const numeric=Number(value)
 if(!Number.isFinite(numeric))return String(value??'—')
 if(field.kind==='scientific')return numeric.toExponential(4)
 if(field.kind==='percent')return `${numeric}${field.unit??'%'}`
 if(field.kind==='duration'||field.kind==='unit_number')return `${numeric.toLocaleString()} ${field.unit??''}`.trim()
 return numeric.toLocaleString()
}

export function FieldValue({field,value}:{field:FieldDefinition;value:unknown}){
 if(value==null||value==='')return <span className="muted">—</span>
 if(field.kind==='boolean')return <span>{value?'Yes':'No'}</span>
 if(field.kind==='json'||field.kind==='object'||field.kind==='array'||field.kind==='formula'||field.kind==='computed')return <pre className="field-structured-value"><code>{typeof value==='string'?value:JSON.stringify(value,null,2)}</code></pre>
 if(field.kind==='multiselect'||field.kind==='multi_enum')return <span className="field-chip-list">{(Array.isArray(value)?value:[]).map(item=><span className="field-chip" key={String(item)}>{String(item).replaceAll('_',' ')}</span>)}</span>
 if(field.kind==='code')return <pre className="field-structured-value"><code>{String(value)}</code></pre>
 if(field.kind==='markdown')return <div className="field-markdown-source">{String(value)}</div>
 if(['integer','number','decimal','percent','duration','scientific','unit_number','range','tolerance'].includes(field.kind))return <span className="tabular-value">{displayNumber(value,field)}</span>
 if(field.kind==='datetime')return <time dateTime={String(value)}>{new Date(String(value)).toLocaleString()}</time>
 if(field.kind==='date')return <time dateTime={String(value)}>{String(value)}</time>
 return <span>{String(value)}</span>
}
