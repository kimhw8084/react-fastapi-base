import { useState, type ReactNode } from 'react'
import { OverlayShell } from './OverlayShell'

interface Props {
  title: string
  subtitle?: ReactNode
  status?: ReactNode
  children: ReactNode
  footer?: ReactNode
  onClose: () => void
  dirty?: boolean
  busy?: boolean
  wide?: boolean
  expandable?: boolean
}
export function Dialog({ title, subtitle, status, children, footer, onClose, dirty = false, busy = false, wide = false, expandable = wide }: Props) {
  const [discard, setDiscard] = useState(false)
  const close = () => { if (busy) return; if (dirty) setDiscard(true); else onClose() }
  return <>
    <OverlayShell open kind="modal" title={title} subtitle={subtitle} status={status} footer={footer} onClose={close} busy={busy} wide={wide} expandable={expandable}>{children}</OverlayShell>
    {discard && <Dialog title="Discard unsaved changes?" onClose={() => setDiscard(false)} footer={<><button onClick={() => setDiscard(false)}>Keep editing</button><button className="danger" onClick={() => { setDiscard(false); onClose() }}>Discard changes</button></>}><p>Your changes have not been saved. Discard only this draft?</p></Dialog>}
  </>
}
