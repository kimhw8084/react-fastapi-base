export type ColorModePreference='system'|'light'|'dark'
export type ResolvedColorMode='light'|'dark'
export function resolveColorMode(preference:ColorModePreference,prefersDark:boolean):ResolvedColorMode{return preference==='system'?(prefersDark?'dark':'light'):preference}
export function isColorModePreference(value:unknown):value is ColorModePreference{return value==='system'||value==='light'||value==='dark'}
