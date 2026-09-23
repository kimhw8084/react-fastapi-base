export function gridHeightForRows(rowCount:number,density:'comfortable'|'compact'){
 const rowHeight=density==='compact'?40:52
 return Math.min(520,Math.max(112,44+Math.max(0,rowCount)*rowHeight+2))
}
