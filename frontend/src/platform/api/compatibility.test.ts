import { describe, expect, it } from 'vitest'
import { API_CONTRACT_REVISION, API_MAJOR, type Bootstrap } from '../../generated/schema'
import { ApiError, validateApiCompatibility } from './client'

const bootstrap = (overrides: Partial<Bootstrap> = {}): Bootstrap => ({
  user_id: 'alice', profile: 'development', csrf_token: 'token', tenants: [],
  application: {} as Bootstrap['application'], build_version: '1.0.0-rc.9',
  api_major: API_MAJOR, api_revision: API_CONTRACT_REVISION, ...overrides,
})

describe('API compatibility handshake', () => {
  it('accepts the same major and a newer compatible backend revision', () => {
    expect(validateApiCompatibility(bootstrap({ api_revision: API_CONTRACT_REVISION + 1 })).api_major).toBe(API_MAJOR)
  })

  it.each([
    ['missing metadata', { api_major: undefined, api_revision: undefined }, 'api_contract_metadata_missing'],
    ['major mismatch', { api_major: API_MAJOR + 1 }, 'api_major_mismatch'],
    ['older revision', { api_revision: API_CONTRACT_REVISION - 1 }, 'api_revision_too_old'],
  ])('rejects %s before feature calls', (_label, overrides, code) => {
    expect(() => validateApiCompatibility(bootstrap(overrides as Partial<Bootstrap>))).toThrow(ApiError)
    try { validateApiCompatibility(bootstrap(overrides as Partial<Bootstrap>)) } catch (error) { expect(error).toMatchObject({ code }) }
  })
})
