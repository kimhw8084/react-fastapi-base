import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { catalogVariants } from './generatedVariants'
import { CatalogVariant, CatalogVariantGallery } from './variants'

describe('catalog variant registry', () => {
it('every required catalog variant has a real generic renderer', () => {
  render(<CatalogVariantGallery />)
  expect(catalogVariants).toHaveLength(605)
  expect(screen.getAllByRole('region').length).toBeGreaterThan(0)
  const renderedLabels = new Set(Array.from(document.querySelectorAll<HTMLElement>('[aria-label]'), element => element.getAttribute('aria-label')))
  for (const variant of catalogVariants) expect(renderedLabels.has(variant.id)).toBe(true)
}, 30000)

it('family renderer remains usable when the catalog is filtered', () => {
  const sample = catalogVariants.filter(variant => ['form','grid','chart','surface'].includes(variant.family))
  render(<>{sample.map(variant=><CatalogVariant key={variant.id} variant={variant}/>)}</>)
  for (const variant of sample) expect(screen.getAllByLabelText(variant.id).length).toBeGreaterThan(0)
})
})
