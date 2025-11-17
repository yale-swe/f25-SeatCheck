import { describe, it, expect } from 'vitest'
import { Colors } from '../constants/theme'

describe('Theme Colors', () => {
  it('light mode has text color', () => {
    expect(Colors.light.text).toBeDefined()
    expect(Colors.light.text.length).toBeGreaterThan(0)
  })

  it('dark mode has text color', () => {
    expect(Colors.dark.text).toBeDefined()
    expect(Colors.dark.text.length).toBeGreaterThan(0)
  })

  it('light and dark text colors are different', () => {
    expect(Colors.light.text).not.toBe(Colors.dark.text)
  })

  it('light mode has all required colors', () => {
    const requiredColors = ['text', 'background', 'tint', 'icon', 'tabIconDefault', 'tabIconSelected']
    requiredColors.forEach(colorName => {
      expect(Colors.light[colorName]).toBeDefined()
    })
  })

  it('dark mode has all required colors', () => {
    const requiredColors = ['text', 'background', 'tint', 'icon', 'tabIconDefault', 'tabIconSelected']
    requiredColors.forEach(colorName => {
      expect(Colors.dark[colorName]).toBeDefined()
    })
  })

  it('tint colors are different between light and dark', () => {
    expect(Colors.light.tint).not.toBe(Colors.dark.tint)
  })
})
