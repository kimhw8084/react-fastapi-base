import {useEffect, type ReactNode} from 'react'
import type { Preview } from '@storybook/react-vite'
import '../../experience-lab/public/styles.css'
function ThemeBoundary({children,theme,density}:{children:ReactNode;theme:string;density:string}){
  useEffect(()=>{document.documentElement.dataset.theme=theme;document.documentElement.dataset.density=density;return()=>{delete document.documentElement.dataset.theme;delete document.documentElement.dataset.density}},[theme,density])
  return <div style={{padding:24,background:'var(--page)',minHeight:'100vh'}}><div className="panel">{children}</div></div>
}
const preview:Preview={
  globalTypes:{
    theme:{description:'Semantic appearance',toolbar:{icon:'paintbrush',items:['light','dark']}},
    density:{description:'Content density',toolbar:{items:['comfortable','compact']}},
  },
  initialGlobals:{theme:'light',density:'comfortable'},
  parameters:{layout:'fullscreen',a11y:{test:'error'}},
  decorators:[(Story,context)=><ThemeBoundary theme={String(context.globals.theme??'light')} density={String(context.globals.density??'comfortable')}><Story/></ThemeBoundary>],
}
export default preview
