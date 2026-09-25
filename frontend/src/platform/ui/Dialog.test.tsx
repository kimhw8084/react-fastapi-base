import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useState } from 'react'
import { Dialog } from './Dialog'
describe('dirty dialog ownership',()=>{
 it('opens a named dialog',()=>{render(<Dialog title="Edit record" onClose={()=>{}}>Fields</Dialog>);expect(screen.getByRole('dialog',{name:'Edit record'})).toBeVisible()})
 it('clean close delegates once',()=>{const close=vi.fn();render(<Dialog title="Details" onClose={close}>Body</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Details'}));expect(close).toHaveBeenCalledTimes(1)})
 it('dirty close requires explicit discard',()=>{const close=vi.fn();render(<Dialog title="Edit" onClose={close} dirty>Fields</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Edit'}));expect(close).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Discard changes'}));expect(close).toHaveBeenCalledTimes(1)})
 it('keeping a draft does not dismiss the parent',()=>{const close=vi.fn();render(<Dialog title="Edit" onClose={close} dirty>Fields</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Edit'}));fireEvent.click(screen.getByRole('button',{name:'Keep editing'}));expect(close).not.toHaveBeenCalled();expect(screen.getByRole('dialog',{name:'Edit'})).toBeVisible()})
 it('busy operations cannot be dismissed',()=>{const close=vi.fn();render(<Dialog title="Saving" onClose={close} busy>Fields</Dialog>);expect(screen.getByRole('button',{name:'Close Saving'})).toBeDisabled();expect(close).not.toHaveBeenCalled()})
})

describe('overlay focus eligibility',()=>{
 beforeEach(()=>{vi.spyOn(HTMLElement.prototype,'getClientRects').mockReturnValue({length:1,item:()=>null} as unknown as DOMRectList)})
 afterEach(()=>vi.restoreAllMocks())
 function fixture(){
  function Example(){const [open,setOpen]=useState(false);const [showOpener,setShowOpener]=useState(true);return <>{showOpener&&<button onClick={()=>setOpen(true)}>Open dialog</button>}<button onClick={()=>setShowOpener(false)}>Remove opener</button>{open&&<Dialog title="Details" onClose={()=>setOpen(false)}><button>Inside action</button></Dialog>}<main id="main-content" tabIndex={-1}>Task content</main></>}
  return render(<Example/>)
 }
 it('returns focus to a still eligible invoker',async()=>{
  fixture();const opener=screen.getByRole('button',{name:'Open dialog'});opener.focus();fireEvent.click(opener);fireEvent.click(screen.getByRole('button',{name:'Close Details'}));await waitFor(()=>expect(opener).toHaveFocus())
 })
 it.each([
  ['disabled',(node:HTMLElement)=>{(node as HTMLButtonElement).disabled=true}],
  ['display hidden',(node:HTMLElement)=>{node.style.display='none'}],
  ['visibility hidden',(node:HTMLElement)=>{node.style.visibility='hidden'}],
  ['aria hidden',(node:HTMLElement)=>{node.setAttribute('aria-hidden','true')}],
  ['inert',(node:HTMLElement)=>{node.setAttribute('inert','')}],
  ['removed',null],
 ])('moves focus to the main task when the %s invoker is ineligible',async(_case,makeIneligible)=>{
  fixture();const opener=screen.getByRole('button',{name:'Open dialog'});opener.focus();fireEvent.click(opener);if(makeIneligible)makeIneligible(opener);else fireEvent.click(screen.getByRole('button',{name:'Remove opener'}));fireEvent.click(screen.getByRole('button',{name:'Close Details'}));await waitFor(()=>expect(screen.getByRole('main')).toHaveFocus())
 })
 it('returns a nested overlay to its eligible parent owner',async()=>{
  function Nested(){const [parent,setParent]=useState(false);const [child,setChild]=useState(false);return <><button onClick={()=>setParent(true)}>Open parent</button>{parent&&<Dialog title="Parent" onClose={()=>setParent(false)}><button onClick={()=>setChild(true)}>Open child</button>{child&&<Dialog title="Child" onClose={()=>setChild(false)}><p>Nested work</p></Dialog>}</Dialog>}<main id="main-content" tabIndex={-1}>Task content</main></>}
  render(<Nested/>);fireEvent.click(screen.getByRole('button',{name:'Open parent'}));const parentButton=screen.getByRole('button',{name:'Open child'});parentButton.focus();fireEvent.click(parentButton);fireEvent.click(screen.getByRole('button',{name:'Close Child'}));await waitFor(()=>expect(parentButton).toHaveFocus())
 })
})
