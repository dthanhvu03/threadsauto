import { describe, it, expect } from 'vitest'
import {
  chartColors,
  platformColors,
  statusColors,
  getPlatformColor,
  getStatusColor,
  formatChartDate,
  aggregateByKey
} from '@/utils/chartConfig'

describe('chartConfig', () => {
  describe('getPlatformColor', () => {
    it('returns correct color for THREADS', () => {
      expect(getPlatformColor('THREADS')).toBe(platformColors.THREADS)
    })

    it('returns correct color for FACEBOOK', () => {
      expect(getPlatformColor('FACEBOOK')).toBe(platformColors.FACEBOOK)
    })

    it('returns default color for unknown platform', () => {
      expect(getPlatformColor('UNKNOWN')).toBe(platformColors.default)
    })
  })

  describe('getStatusColor', () => {
    it('returns correct color for pending', () => {
      expect(getStatusColor('pending')).toBe(statusColors.pending)
    })

    it('returns correct color for completed', () => {
      expect(getStatusColor('completed')).toBe(statusColors.completed)
    })

    it('returns correct color for failed', () => {
      expect(getStatusColor('failed')).toBe(statusColors.failed)
    })
  })

  describe('formatChartDate', () => {
    it('formats date correctly', () => {
      const date = '2024-01-15T10:30:00Z'
      const formatted = formatChartDate(date)
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('handles null date', () => {
      expect(formatChartDate(null)).toBe('')
    })
  })

  describe('aggregateByKey', () => {
    it('aggregates data by key', () => {
      const data = [
        { platform: 'THREADS', value: 5 },
        { platform: 'THREADS', value: 3 },
        { platform: 'FACEBOOK', value: 2 }
      ]

      const result = aggregateByKey(data, 'platform', 'value')
      expect(result.THREADS).toBe(8)
      expect(result.FACEBOOK).toBe(2)
    })
  })
})
