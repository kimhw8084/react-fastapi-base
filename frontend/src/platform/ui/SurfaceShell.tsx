import type { ReactNode } from 'react'

export interface SurfaceShellProps {
  title: ReactNode
  subtitle?: ReactNode
  status?: ReactNode
  controls?: ReactNode
  children: ReactNode
  footer?: ReactNode
  className?: string
  titleId?: string
}

export function SurfaceShell({ title, subtitle, status, controls, children, footer, className = '', titleId }: SurfaceShellProps) {
  return <div className={`surface-shell ${className}`.trim()}>
    <header className="surface-header">
      <div className="surface-heading">
        <div className="surface-title-row"><h2 id={titleId}>{title}</h2>{status && <div className="surface-status">{status}</div>}</div>
        {subtitle && <div className="surface-subtitle">{subtitle}</div>}
      </div>
      {controls && <div className="surface-controls" aria-label="Window controls">{controls}</div>}
    </header>
    <div className="surface-body">{children}</div>
    {footer && <footer className="surface-footer">{footer}</footer>}
  </div>
}
