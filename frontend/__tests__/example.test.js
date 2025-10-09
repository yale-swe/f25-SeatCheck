import { describe, it, expect } from 'vitest'

describe('sanity', () => {
  it('adds numbers', () => {
    expect(2 + 3).toBe(5)
  })

  it('truthiness', () => {
    expect(Boolean('SeatCheck')).toBe(true)
  })
})
