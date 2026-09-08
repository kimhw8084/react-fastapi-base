/** Explicit, testable Tab containment in addition to native <dialog> modality. */
export function containDialogFocus(dialog:HTMLDialogElement):void {
 const focusable=()=>Array.from(dialog.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(el=>el.getClientRects().length>0&&!el.closest('[hidden],[inert]'));
 dialog.addEventListener('keydown',e=>{
  if(e.key!=='Tab')return;
  const nodes=focusable(),first=nodes[0],last=nodes[nodes.length-1];
  if(!first||!last){e.preventDefault();dialog.focus();return;}
  if(e.shiftKey&&(document.activeElement===first||!dialog.contains(document.activeElement))){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&(document.activeElement===last||!dialog.contains(document.activeElement))){e.preventDefault();first.focus();}
 });
}
