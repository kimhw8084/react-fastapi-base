import { useState, type ReactNode } from 'react'
import { Dialog } from './Dialog'
import { BottomSheetShell, OverlayShell, PeekShell } from './OverlayShell'
import { DrawerShell, InspectorShell, PanelShell, type PanelShellProps } from './PanelShell'
import { FloatingPanelShell } from './FloatingPanelShell'

interface CommonDialogProps{open:boolean;title:string;subtitle?:ReactNode;children:ReactNode;onClose:()=>void;footer?:ReactNode;dirty?:boolean;busy?:boolean}
export function AlertDialog({open,...props}:CommonDialogProps){return open?<Dialog {...props}/>:null}
export function ConfirmDialog({open,title,description,confirmLabel='Confirm',cancelLabel='Cancel',onConfirm,onClose,busy=false}:{open:boolean;title:string;description:ReactNode;confirmLabel?:string;cancelLabel?:string;onConfirm:()=>void;onClose:()=>void;busy?:boolean}){return open?<Dialog title={title} onClose={onClose} busy={busy} footer={<><button type="button" onClick={onClose} disabled={busy}>{cancelLabel}</button><button type="button" onClick={onConfirm} disabled={busy}>{confirmLabel}</button></>}><p>{description}</p></Dialog>:null}
export function DestructiveConfirmDialog(props:Parameters<typeof ConfirmDialog>[0]){return <ConfirmDialog {...props} confirmLabel={props.confirmLabel??'Delete'} onConfirm={props.onConfirm}/>}
export function FormDialog(props:CommonDialogProps&{wide?:boolean}){return props.open?<Dialog {...props} wide={props.wide??true}/>:null}
export function DossierDialog(props:CommonDialogProps){return props.open?<Dialog {...props} wide expandable/>:null}
export function FullScreenDialog({open,title,subtitle,children,onClose,footer,busy=false}:{open:boolean;title:string;subtitle?:ReactNode;children:ReactNode;onClose:()=>void;footer?:ReactNode;busy?:boolean}){return <OverlayShell open={open} kind="fullscreen" title={title} subtitle={subtitle} onClose={onClose} footer={footer} busy={busy} wide expandable>{children}</OverlayShell>}
export function DesignerShell(props:Parameters<typeof FullScreenDialog>[0]){return <FullScreenDialog {...props}/>}
export function ComparisonDialog({open,title='Compare records',left,right,onClose}:{open:boolean;title?:string;left:ReactNode;right:ReactNode;onClose:()=>void}){return open?<Dialog title={title} onClose={onClose} wide expandable><div className="comparison-shell"><section>{left}</section><section>{right}</section></div></Dialog>:null}
export function WizardDialog({open,title,steps,activeStep,onStepChange,onClose,children,onFinish,finishLabel='Finish'}:{open:boolean;title:string;steps:string[];activeStep:number;onStepChange:(step:number)=>void;onClose:()=>void;children:ReactNode;onFinish?:()=>void;finishLabel?:string}){const last=activeStep>=steps.length-1;return open?<Dialog title={title} subtitle={`Step ${activeStep+1} of ${steps.length}`} onClose={onClose} wide footer={<><button type="button" disabled={activeStep===0} onClick={()=>onStepChange(Math.max(0,activeStep-1))}>Back</button>{last?<button type="button" onClick={onFinish??onClose}>{finishLabel}</button>:<button type="button" onClick={()=>onStepChange(Math.min(steps.length-1,activeStep+1))}>Next</button>}</>}><ol className="wizard-steps">{steps.map((step,index)=><li key={step} className={index===activeStep?'active':index<activeStep?'complete':''}><button type="button" onClick={()=>onStepChange(index)} aria-current={index===activeStep?'step':undefined}>{index+1}. {step}</button></li>)}</ol>{children}</Dialog>:null}

export function DrawerLeft(props:Parameters<typeof DrawerShell>[0]){return <div className="drawer-left"><DrawerShell {...props}/></div>}
export const DrawerRight=DrawerShell
export function DrawerBottom({open,onClose,...props}:PanelShellProps&{open:boolean;onClose:()=>void}){return <BottomSheetShell open={open} title={props.title} subtitle={props.subtitle} status={props.status} footer={props.footer} onClose={onClose}>{props.children}</BottomSheetShell>}
export const InspectorDrawer=DrawerShell
export const DetailsDrawer=DrawerShell
export const SideSheet=DrawerBottom
export const FloatingInspector=InspectorShell
export const DockedPanel=InspectorShell
export const SidecarPanel=PanelShell
export const CollapsiblePanel=PanelShell

export function PopoverShell({open,anchor,onClose,title,children,width=260}:{open:boolean;anchor:{x:number;y:number}|null;onClose:()=>void;title?:ReactNode;children:ReactNode;width?:number}){return <FloatingPanelShell open={open} anchor={anchor??{x:16,y:16}} onClose={onClose} title={title} width={width}>{children}</FloatingPanelShell>}
export const DropdownShell=PopoverShell
export const ComboDropdownShell=PopoverShell
export const HoverCardShell=PopoverShell
export const ContextMenuShell=PopoverShell
export const ActionMenuShell=PopoverShell
export const AnchoredFlyoutShell=PopoverShell
export const SearchPaletteShell=PeekShell
export const QuickSwitcherShell=PeekShell

export function NotificationDrawer({open,onClose,title='Notifications',children}:{open:boolean;onClose:()=>void;title?:ReactNode;children:ReactNode}){return <DrawerShell open={open} onClose={onClose} title={title}>{children}</DrawerShell>}

export function useWizard(stepCount:number,initial=0){const[step,setStep]=useState(Math.max(0,Math.min(initial,stepCount-1)));return{step,setStep,next:()=>setStep(value=>Math.min(stepCount-1,value+1)),back:()=>setStep(value=>Math.max(0,value-1)),reset:()=>setStep(initial)}}
