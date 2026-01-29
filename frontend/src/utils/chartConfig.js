/**
 * Chart.js configuration helpers.
 * 
 * Provides default configurations matching the design system.
 */

// Design system colors (monochrome professional)
export const chartColors = {
  primary: '#111111',
  secondary: '#6b7280',
  silver: '#9ca3af',
  success: '#16a34a',
  warning: '#d97706',
  error: '#dc2626',
  info: '#4b5563',
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827'
  }
}

// Platform colors
export const platformColors = {
  THREADS: chartColors.primary,
  FACEBOOK: chartColors.secondary,
  default: chartColors.silver
}

// Status colors
export const statusColors = {
  pending: chartColors.warning,
  completed: chartColors.success,
  failed: chartColors.error,
  running: chartColors.info,
  scheduled: chartColors.secondary
}

/**
 * Get responsive chart options based on screen size.
 */
export function getResponsiveChartOptions(customOptions = {}) {
  // Check if we're in browser environment
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768
  
  // Merge with custom options, preserving custom plugins
  const mergedPlugins = {
    legend: {
      display: true,
      position: isMobile ? 'bottom' : 'top',
      labels: {
        usePointStyle: true,
        padding: isMobile ? 10 : 15,
        font: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: isMobile ? 11 : 12
        }
      }
    },
    ...(customOptions.plugins || {})
  }
  
  // If custom plugins has legend, merge it
  if (customOptions.plugins?.legend) {
    mergedPlugins.legend = {
      ...mergedPlugins.legend,
      ...customOptions.plugins.legend
    }
  }
  
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: mergedPlugins,
    ...customOptions,
    // Override plugins with merged version
    plugins: mergedPlugins
  }
}

/**
 * Default chart options matching design system.
 */
export const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 15,
        font: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 12
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 13,
        weight: 'bold'
      },
      bodyFont: {
        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 12
      },
      borderColor: chartColors.gray[200],
      borderWidth: 1,
      cornerRadius: 6,
      callbacks: {
        title: (context) => {
          // Format title with VN datetime if it's a date
          const label = context[0]?.label || ''
          // If label looks like a date, try to format it
          if (label && /^\d{2}\/\d{2}\/\d{4}/.test(label)) {
            return label
          }
          return label
        },
        label: (context) => {
          const label = context.dataset.label || ''
          const value = context.parsed.y ?? context.parsed ?? ''
          return `${label}: ${value}`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 11
        },
        color: chartColors.gray[600]
      }
    },
    y: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        drawBorder: false
      },
      ticks: {
        font: {
          family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 11
        },
        color: chartColors.gray[600]
      }
    }
  }
}

/**
 * Get color for platform.
 */
export function getPlatformColor(platform) {
  return platformColors[platform?.toUpperCase()] || platformColors.default
}

/**
 * Get color for status.
 */
export function getStatusColor(status) {
  return statusColors[status?.toLowerCase()] || chartColors.gray[500]
}

import { formatDateVN, formatDateTimeVN } from './datetime'

/**
 * Format date for chart display.
 * Uses Vietnam timezone formatting.
 */
export function formatChartDate(date) {
  if (!date) return ''
  return formatDateVN(date)
}

/**
 * Format date time for chart display.
 * Uses Vietnam timezone formatting.
 */
export function formatChartDateTime(date) {
  if (!date) return ''
  // For charts, we might want shorter format, so use date + time without seconds
  const formatted = formatDateTimeVN(date)
  // Remove seconds for chart display: "dd/MM/yyyy HH:mm:ss" -> "dd/MM/yyyy HH:mm"
  return formatted ? formatted.slice(0, -3) : ''
}

/**
 * Group data by date.
 */
export function groupByDate(data, dateKey = 'date', valueKey = 'value') {
  const grouped = {}
  data.forEach(item => {
    const date = new Date(item[dateKey]).toDateString()
    if (!grouped[date]) {
      grouped[date] = []
    }
    grouped[date].push(item[valueKey])
  })
  return grouped
}

/**
 * Aggregate data by key.
 */
export function aggregateByKey(data, key, valueKey = 'value') {
  const aggregated = {}
  data.forEach(item => {
    const k = item[key]
    aggregated[k] = (aggregated[k] || 0) + (item[valueKey] || 1)
  })
  return aggregated
}
