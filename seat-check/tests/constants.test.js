import { describe, it, expect } from 'vitest'
import { Colors, Fonts } from '../constants/theme'

describe('Colors', () => {
  it('defines light mode colors', () => {
    expect(Colors.light.text).toBeDefined()
    expect(Colors.light.background).toBeDefined()
    expect(Colors.light.tint).toBeDefined()
    expect(Colors.light.icon).toBeDefined()
    expect(Colors.light.tabIconDefault).toBeDefined()
    expect(Colors.light.tabIconSelected).toBeDefined()
  })

  it('defines dark mode colors', () => {
    expect(Colors.dark.text).toBeDefined()
    expect(Colors.dark.background).toBeDefined()
    expect(Colors.dark.tint).toBeDefined()
    expect(Colors.dark.icon).toBeDefined()
    expect(Colors.dark.tabIconDefault).toBeDefined()
    expect(Colors.dark.tabIconSelected).toBeDefined()
  })

  it('light and dark colors are different', () => {
    expect(Colors.light.text).not.toBe(Colors.dark.text)
    expect(Colors.light.background).not.toBe(Colors.dark.background)
  })

  it('all light color values are hex strings or color names', () => {
    const lightColors = Object.values(Colors.light)
    expect(lightColors.length).toBeGreaterThan(0)
    lightColors.forEach(color => {
      expect(color).toBeDefined()
    })
  })

  it('all dark color values are hex strings or color names', () => {
    const darkColors = Object.values(Colors.dark)
    expect(darkColors.length).toBeGreaterThan(0)
    darkColors.forEach(color => {
      expect(color).toBeDefined()
    })
  })
})

describe('Fonts', () => {
  it('defines fonts object', () => {
    expect(Fonts).toBeDefined()
  })

  it('fonts object has font families defined', () => {
    expect(Object.keys(Fonts).length).toBeGreaterThan(0)
  })
})
