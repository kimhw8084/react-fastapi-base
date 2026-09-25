import type { SVGProps } from 'react'

export const ICON_KEYS=['work-items','projects','racks','equipment','knowledge','investigations','research','risks','planning','diagrams','measurements','wafers','lots','equipment-states','recipes','services','delivery','observability','incidents','objectives','system','command','refresh','add','quick-look','close','expand','chevron','search','copy','star','star-outline','pin','pin-outline','external','view','sort-ascending','sort-descending','trend-up','trend-down','trend-flat','zoom-in','zoom-out'] as const
export type IconKey=typeof ICON_KEYS[number]

const paths:Record<IconKey,string>={
 'work-items':'M7 4h10v3h4v14H3V7h4V4Zm0 3h10V6H7v1Zm0 5h10M7 16h7',
 projects:'M3 7h7l2 2h9v11H3V7Zm0 0V5h7l2 2',
 racks:'M4 4h16v5H4zM4 11h16v5H4zM4 18h16v2H4zM7 6.5h.01M7 13.5h.01',
 equipment:'M9 3v3m6-3v3M9 18v3m6-3v3M3 9h3m12 0h3M3 15h3m12 0h3M7 6h10v12H7zM10 9h4v6h-4z',
 knowledge:'M4 5.5A3.5 3.5 0 0 1 7.5 2H20v18H7.5A3.5 3.5 0 0 0 4 23V5.5Zm0 0V20m4-13h8m-8 4h8',
 investigations:'M10 18a7 7 0 1 1 5.4-2.6L21 21m-11-9 2-2 2 2-2 2-2-2Z',
 research:'M9 3h6m-5 0v6L4 19a2 2 0 0 0 1.7 3h12.6a2 2 0 0 0 1.7-3l-6-10V3M7 17h10m-7-4h4',
 risks:'M12 3 20 6v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-3Zm-3 9 2 2 4-5',
 planning:'M5 4v3m14-3v3M4 8h16v13H4zM8 12h3m2 0h3m-8 4h3m2 0h3',
 diagrams:'M5 5h4v4H5zM15 15h4v4h-4zM17 5h2v4h-2zM9 7h8m-9 1 7 8',
 measurements:'M3 19h18M5 16l4-5 3 2 6-8m0 0v4m0-4h-4',
 wafers:'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-6 3 12 12m0-12L6 18m-3-6h18',
 lots:'M4 7 12 3l8 4v10l-8 4-8-4V7Zm0 0 8 4 8-4m-8 4v10',
 'equipment-states':'M4 17a8 8 0 1 1 16 0M12 12l4-4m-4 9h.01M5 21h14',
 recipes:'M4 6h16M4 12h16M4 18h16M8 4v4m8 2v4m-5 2v4',
 services:'M6 18h12a4 4 0 0 0 .6-8A6.5 6.5 0 0 0 6 8.5 4.8 4.8 0 0 0 6 18Z',
 delivery:'M4 17 20 4l-6 16-3-7-7-3Zm7 0 4 3',
 observability:'M3 12h4l3-7 4 14 3-7h4',
 incidents:'M12 3 22 20H2L12 3Zm0 6v5m0 3h.01',
 objectives:'M12 3v3m0 12v3M3 12h3m12 0h3M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Zm0 2v3l2 1',
 system:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm0-6v3m0 14v3M2 12h3m14 0h3M4.9 4.9 7 7m10 10 2.1 2.1m0-14.2L17 7M7 17l-2.1 2.1',
 command:'M8 7 3 12l5 5m8-10 5 5-5 5m-3-12-2 14',
 refresh:'M20 7v5h-5M4 17v-5h5m9-3a7 7 0 0 0-12-2L4 12m16 0-2 5a7 7 0 0 1-12 0',
 add:'M12 5v14M5 12h14',
 'quick-look':'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z',
 close:'M5 5l14 14M19 5 5 19',
 expand:'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5',
 chevron:'m7 10 5 5 5-5',
 search:'M10.5 3a7.5 7.5 0 1 0 0 15 7.5 7.5 0 0 0 0-15ZM16 16l5 5',
 copy:'M8 8h12v13H8zM4 16H3V3h12v2',
 star:'m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z',
 'star-outline':'m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z',
 pin:'M8 3h8l-1 6 3 3v2h-5v7l-1 1-1-1v-7H6v-2l3-3-1-6Z',
 'pin-outline':'M8 3h8l-1 6 3 3v2h-5v7l-1 1-1-1v-7H6v-2l3-3-1-6Z',
 external:'M14 4h6v6m0-6-9 9M18 13v6H4V5h6',
 view:'M3 4h8v7H3zM13 4h8v7h-8zM3 13h8v7H3zM13 13h8v7h-8z',
 'sort-ascending':'M4 7h10M4 12h7M4 17h4m9 3V4m0 0-3 3m3-3 3 3',
 'sort-descending':'M4 7h4M4 12h7M4 17h10m3-13v16m0 0-3-3m3 3 3-3',
 'trend-up':'M4 17 10 11l4 4 6-8m-5 0h5v5',
 'trend-down':'M4 7 10 13l4-4 6 8m-5 0h5v-5',
 'trend-flat':'M4 12h16m-4-4 4 4-4 4',
 'zoom-in':'M10.5 3a7.5 7.5 0 1 0 0 15 7.5 7.5 0 0 0 0-15ZM16 16l5 5M10.5 7v7m-3.5-3.5h7',
 'zoom-out':'M10.5 3a7.5 7.5 0 1 0 0 15 7.5 7.5 0 0 0 0-15ZM16 16l5 5M7 10.5h7',
}

export function Icon({name,size=16,...props}:SVGProps<SVGSVGElement>&{name:IconKey;size?:number}){
 return <svg {...props} width={size} height={size} viewBox="0 0 24 24" fill={name==='star'?'currentColor':'none'} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]}/></svg>
}
