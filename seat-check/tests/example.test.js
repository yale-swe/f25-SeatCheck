import { describe, it, expect } from 'vitest'

describe('basic math', () => {
  it('adds numbers correctly', () => {
    const result = 2 + 3
    expect(result).toBe(5)
  })

  it('subtracts numbers correctly', () => {
    const result = 10 - 4
    expect(result).toBe(6)
  })
})
