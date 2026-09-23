const focusableSelector='a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]'

export function isFocusEligible(node:HTMLElement|null,allowProgrammatic=false):boolean{
 if(!node||!node.isConnected||node.matches(':disabled,[aria-disabled="true"]'))return false
 if(node.getAttribute('tabindex')==="-1"&&!allowProgrammatic)return false
 if(!node.matches(focusableSelector))return false
 for(let current:HTMLElement|null=node;current;current=current.parentElement){
  if(current.hasAttribute('inert')||current.getAttribute('aria-hidden')==='true'||current.getAttribute('aria-disabled')==='true')return false
  const style=window.getComputedStyle(current)
  if(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse'||style.contentVisibility==='hidden'||style.opacity==='0')return false
 }
 return node.getClientRects().length>0
}

export function focusables(root:HTMLElement|null){return root?Array.from(root.querySelectorAll<HTMLElement>(focusableSelector)).filter(node=>isFocusEligible(node)):[]}

export function restoreOverlayFocus(previous:HTMLElement|null,closedOverlay:HTMLElement|null){
 if(previous&&isFocusEligible(previous)){previous.focus();return}
 const owner=previous?.closest<HTMLElement>('.overlay-surface')
 if(owner&&owner!==closedOverlay&&isFocusEligible(owner,true)){
  const candidate=focusables(owner)[0]??owner
  if(isFocusEligible(candidate,true)){candidate.focus();return}
 }
 const main=document.getElementById('main-content')
 if(main&&isFocusEligible(main,true))main.focus()
}
