import { Component, type ErrorInfo, type ReactNode } from 'react'
interface Props { children: ReactNode }
interface State { failed: boolean }
export class ErrorBoundary extends Component<Props,State> {
  state: State = {failed:false}
  static getDerivedStateFromError(): State {return {failed:true}}
  componentDidCatch(_error: Error,_info: ErrorInfo) { /* Do not serialize component data or secrets into a client report. */ }
  render() {
    if(this.state.failed) return <main className="startup"><h1>The workspace could not render</h1><p role="alert">Reload the page. Unsaved form changes may be lost. Report the failing workflow to your support contact; do not share confidential record content.</p><button onClick={()=>window.location.reload()}>Reload application</button></main>
    return this.props.children
  }
}
