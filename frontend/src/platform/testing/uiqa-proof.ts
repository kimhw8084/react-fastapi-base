export class DimensionProofError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DimensionProofError'
  }
}

type ProofAssertion = () => void | Promise<void>

/** Runtime evidence collector for one executable UI state-matrix row. */
export class RuntimeDimensionProof {
  private readonly allowed: ReadonlySet<string>
  private readonly required: ReadonlySet<string>
  private readonly observed = new Set<string>()

  constructor(requiredDimensions: readonly string[], allowedDimensions: readonly string[]) {
    this.allowed = new Set(allowedDimensions)
    this.required = new Set(requiredDimensions)
    if (this.required.size !== requiredDimensions.length) throw new DimensionProofError('Required proof dimensions contain duplicates.')
    if (this.allowed.size !== allowedDimensions.length) throw new DimensionProofError('Allowed proof dimensions contain duplicates.')
    const unknownRequired = requiredDimensions.filter(dimension => !this.allowed.has(dimension))
    if (unknownRequired.length) throw new DimensionProofError(`Required proof dimensions are unknown: ${unknownRequired.sort().join(', ')}.`)
  }

  async prove(dimension: string, assertion: ProofAssertion): Promise<void> {
    if (!this.allowed.has(dimension)) throw new DimensionProofError(`Unknown proof dimension: ${dimension}.`)
    await assertion()
    this.observed.add(dimension)
  }

  observedDimensions(): string[] {
    return [...this.observed].sort()
  }

  complete(): string[] {
    const observed = this.observedDimensions()
    const missing = [...this.required].filter(dimension => !this.observed.has(dimension)).sort()
    const extra = observed.filter(dimension => !this.required.has(dimension))
    if (missing.length || extra.length) {
      const missingText = missing.length ? ` missing=${missing.join(',')}` : ''
      const extraText = extra.length ? ` extra=${extra.join(',')}` : ''
      throw new DimensionProofError(`Runtime proof dimensions do not exactly match the row.${missingText}${extraText}`)
    }
    return observed
  }
}
