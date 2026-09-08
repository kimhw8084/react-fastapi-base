import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
afterEach(cleanup)
// DOM-only component tests do not claim browser focus/geometry verification.
if (!HTMLDialogElement.prototype.showModal) HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
if (!HTMLDialogElement.prototype.close) HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}
