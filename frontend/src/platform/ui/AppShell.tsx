import type { ReactNode } from 'react'
import { SurfaceManagerProvider } from './SurfaceManager'
export function AppShell({sidebar,header,release,children}:{sidebar:ReactNode;header:ReactNode;release?:ReactNode;children:ReactNode}){
  return <SurfaceManagerProvider><div className="application-shell"><a className="skip-link" href="#main-content">Skip to content</a><aside className="sidebar">{sidebar}</aside><div className="application-content"><header className="shell-header">{header}</header>{release&&<div className="release-strip">{release}</div>}<main id="main-content">{children}</main></div></div></SurfaceManagerProvider>
}
