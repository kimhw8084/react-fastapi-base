import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Dialog } from './Dialog'
describe('dirty dialog ownership',()=>{
 it('opens a named dialog',()=>{render(<Dialog title="Edit record" onClose={()=>{}}>Fields</Dialog>);expect(screen.getByRole('dialog',{name:'Edit record'})).toBeVisible()})
 it('clean close delegates once',()=>{const close=vi.fn();render(<Dialog title="Details" onClose={close}>Body</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Details'}));expect(close).toHaveBeenCalledTimes(1)})
 it('dirty close requires explicit discard',()=>{const close=vi.fn();render(<Dialog title="Edit" onClose={close} dirty>Fields</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Edit'}));expect(close).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Discard changes'}));expect(close).toHaveBeenCalledTimes(1)})
 it('keeping a draft does not dismiss the parent',()=>{const close=vi.fn();render(<Dialog title="Edit" onClose={close} dirty>Fields</Dialog>);fireEvent.click(screen.getByRole('button',{name:'Close Edit'}));fireEvent.click(screen.getByRole('button',{name:'Keep editing'}));expect(close).not.toHaveBeenCalled();expect(screen.getByRole('dialog',{name:'Edit'})).toBeVisible()})
 it('busy operations cannot be dismissed',()=>{const close=vi.fn();render(<Dialog title="Saving" onClose={close} busy>Fields</Dialog>);expect(screen.getByRole('button',{name:'Close Saving'})).toBeDisabled();expect(close).not.toHaveBeenCalled()})
})
