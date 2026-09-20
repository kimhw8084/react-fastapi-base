import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react'
import { SurfaceManagerProvider } from './SurfaceManager'

type AppShellProps={sidebar:ReactNode;header:ReactNode;release?:ReactNode;children:ReactNode;mobileNavigationLabel?:string;mobileNavigationResetKey?:string}

export function AppShell({sidebar,header,release,children,mobileNavigationLabel='Current workspace',mobileNavigationResetKey}:AppShellProps){
  const [mobileNavigationOpen,setMobileNavigationOpen]=useState(false)
  const [currentNavigationLabel,setCurrentNavigationLabel]=useState(mobileNavigationLabel)
  const triggerRef=useRef<HTMLButtonElement>(null)
  const previousResetKey=useRef(mobileNavigationResetKey)
  const restoreTriggerFocus=()=>window.requestAnimationFrame(()=>triggerRef.current?.focus())
  const closeMobileNavigation=()=>{setMobileNavigationOpen(false);restoreTriggerFocus()}
  useEffect(()=>{
    if(previousResetKey.current!==mobileNavigationResetKey){
      previousResetKey.current=mobileNavigationResetKey
      if(mobileNavigationOpen){setMobileNavigationOpen(false);restoreTriggerFocus()}
    }
  },[mobileNavigationOpen,mobileNavigationResetKey])
  useEffect(()=>{
    if(!mobileNavigationOpen)return
    const onKeyDown=(event:KeyboardEvent)=>{if(event.key==='Escape'){event.preventDefault();closeMobileNavigation()}}
    window.addEventListener('keydown',onKeyDown)
    return()=>window.removeEventListener('keydown',onKeyDown)
  },[mobileNavigationOpen])
  useEffect(()=>{
    const panel=document.getElementById('mobile-navigation-panel')
    if(!panel)return
    const updateCurrentLabel=()=>{
      const active=panel.querySelector<HTMLElement>('[aria-current="page"],.active')
      const label=active?.textContent?.replace('▦','').trim()
      if(label&&label!==currentNavigationLabel){
        setCurrentNavigationLabel(label)
      }
    }
    updateCurrentLabel()
    const observer=new MutationObserver(updateCurrentLabel)
    observer.observe(panel,{attributes:true,childList:true,subtree:true})
    return()=>observer.disconnect()
  },[currentNavigationLabel,mobileNavigationLabel])
  const onSidebarClick=(event:MouseEvent<HTMLElement>)=>{
    if(window.matchMedia('(max-width: 760px)').matches&&(event.target as HTMLElement).closest('a,button'))closeMobileNavigation()
  }
  return <SurfaceManagerProvider><div className="application-shell"><a className="skip-link" href="#main-content">Skip to content</a><div className="mobile-navigation"><button ref={triggerRef} type="button" className="mobile-navigation-toggle" aria-controls="mobile-navigation-panel" aria-expanded={mobileNavigationOpen} onClick={()=>mobileNavigationOpen?closeMobileNavigation():setMobileNavigationOpen(true)}><span className="mobile-navigation-label">Navigation</span><strong>{currentNavigationLabel}</strong><span className="mobile-navigation-caret" aria-hidden="true">⌄</span></button><aside id="mobile-navigation-panel" className={`sidebar${mobileNavigationOpen?' mobile-navigation-open':''}`} onClick={onSidebarClick}>{sidebar}</aside></div><div className="application-content"><header className="shell-header">{header}</header>{release&&<div className="release-strip">{release}</div>}<main id="main-content" tabIndex={-1}>{children}</main></div></div></SurfaceManagerProvider>
}
