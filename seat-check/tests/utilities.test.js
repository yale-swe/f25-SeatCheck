import { describe, it, expect } from 'vitest'
import { Colors, Fonts } from '../constants/theme'

describe('Utility Functions and Constants', () => {
  describe('Colors Constants', () => {
    it('Colors object is defined', () => {
      expect(Colors).toBeDefined()
    })

    it('Colors has light mode', () => {
      expect(Colors.light).toBeDefined()
    })

    it('Colors has dark mode', () => {
      expect(Colors.dark).toBeDefined()
    })

    it('Light mode has text color', () => {
      expect(Colors.light.text).toBeDefined()
      expect(typeof Colors.light.text).toBe('string')
    })

    it('Light mode has background color', () => {
      expect(Colors.light.background).toBeDefined()
    })

    it('Light mode has tint color', () => {
      expect(Colors.light.tint).toBeDefined()
    })

    it('Light mode has icon color', () => {
      expect(Colors.light.icon).toBeDefined()
    })

    it('Light mode has tabIconDefault', () => {
      expect(Colors.light.tabIconDefault).toBeDefined()
    })

    it('Light mode has tabIconSelected', () => {
      expect(Colors.light.tabIconSelected).toBeDefined()
    })

    it('Dark mode has text color', () => {
      expect(Colors.dark.text).toBeDefined()
    })

    it('Dark mode has background color', () => {
      expect(Colors.dark.background).toBeDefined()
    })

    it('Dark mode has tint color', () => {
      expect(Colors.dark.tint).toBeDefined()
    })

    it('Dark mode has icon color', () => {
      expect(Colors.dark.icon).toBeDefined()
    })

    it('Dark mode has tabIconDefault', () => {
      expect(Colors.dark.tabIconDefault).toBeDefined()
    })

    it('Dark mode has tabIconSelected', () => {
      expect(Colors.dark.tabIconSelected).toBeDefined()
    })

    it('Light and dark text colors are different', () => {
      expect(Colors.light.text).not.toBe(Colors.dark.text)
    })

    it('Light and dark background colors are different', () => {
      expect(Colors.light.background).not.toBe(Colors.dark.background)
    })

    it('Light and dark tint colors are different', () => {
      expect(Colors.light.tint).not.toBe(Colors.dark.tint)
    })

    it('All light colors are strings', () => {
      Object.values(Colors.light).forEach(color => {
        expect(typeof color).toBe('string')
        expect(color.length).toBeGreaterThan(0)
      })
    })

    it('All dark colors are strings', () => {
      Object.values(Colors.dark).forEach(color => {
        expect(typeof color).toBe('string')
        expect(color.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Fonts Constants', () => {
    it('Fonts object is defined', () => {
      expect(Fonts).toBeDefined()
    })

    it('Fonts has iOS variant', () => {
      expect(Fonts.ios).toBeDefined()
    })

    it('Fonts has default variant', () => {
      expect(Fonts.default).toBeDefined()
    })

    it('Fonts has web variant', () => {
      expect(Fonts.web).toBeDefined()
    })

    it('iOS fonts have sans', () => {
      expect(Fonts.ios.sans).toBeDefined()
    })

    it('iOS fonts have serif', () => {
      expect(Fonts.ios.serif).toBeDefined()
    })

    it('iOS fonts have rounded', () => {
      expect(Fonts.ios.rounded).toBeDefined()
    })

    it('iOS fonts have mono', () => {
      expect(Fonts.ios.mono).toBeDefined()
    })

    it('Default fonts have sans', () => {
      expect(Fonts.default.sans).toBeDefined()
    })

    it('Default fonts have serif', () => {
      expect(Fonts.default.serif).toBeDefined()
    })

    it('Default fonts have rounded', () => {
      expect(Fonts.default.rounded).toBeDefined()
    })

    it('Default fonts have mono', () => {
      expect(Fonts.default.mono).toBeDefined()
    })

    it('Web fonts have sans', () => {
      expect(Fonts.web.sans).toBeDefined()
    })

    it('Web fonts have serif', () => {
      expect(Fonts.web.serif).toBeDefined()
    })

    it('Web fonts have rounded', () => {
      expect(Fonts.web.rounded).toBeDefined()
    })

    it('Web fonts have mono', () => {
      expect(Fonts.web.mono).toBeDefined()
    })

    it('All font values are strings', () => {
      [Fonts.ios, Fonts.default, Fonts.web].forEach(fontVariant => {
        Object.values(fontVariant).forEach(font => {
          expect(typeof font).toBe('string')
          expect(font.length).toBeGreaterThan(0)
        })
      })
    })

    it('Web fonts are more detailed than defaults', () => {
      expect(Fonts.web.sans.length).toBeGreaterThanOrEqual(Fonts.default.sans.length)
    })
  })

  describe('Color Value Validation', () => {
    it('Light mode colors start with hash or are named colors', () => {
      Object.values(Colors.light).forEach(color => {
        expect(color.startsWith('#') || /^[a-z]+$/i.test(color)).toBe(true)
      })
    })

    it('Dark mode colors start with hash or are named colors', () => {
      Object.values(Colors.dark).forEach(color => {
        expect(color.startsWith('#') || /^[a-z]+$/i.test(color)).toBe(true)
      })
    })

    it('Light colors have contrast', () => {
      // Light mode should have contrasting text and background
      expect(Colors.light.text).not.toBe(Colors.light.background)
    })

    it('Dark colors have contrast', () => {
      // Dark mode should have contrasting text and background
      expect(Colors.dark.text).not.toBe(Colors.dark.background)
    })

    it('Light mode tint color is different from text', () => {
      expect(Colors.light.tint).not.toBe(Colors.light.text)
    })

    it('Dark mode tint color is different from text', () => {
      expect(Colors.dark.tint).not.toBe(Colors.dark.text)
    })
  })
})
