/**
 * Chart.js configuration helpers.
 * 
 * Provides default configurations matching the design system.
 */

// Design System Colors from MASTER.md
// Primary: #2563EB, Secondary: #3B82F6, CTA: #F97316
export const chartColors = {
  // Design system primary colors
  primary: '#2563EB',      // --color-primary
  secondary: '#3B82F6',    // --color-secondary
  cta: '#F97316',          // --color-cta
  // Chart-specific colors (from charts.csv recommendations)
  trendLine: '#0080FF',    // Primary for trend/time-series (charts.csv)
  success: '#16a34a',      // Green for positive/completed
  warning: '#d97706',      // Orange for warnings
  error: '#dc2626',        // Red for errors/failed
  info: '#4b5563',         // Gray for info
  // Gray scale
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

/**
 * Enhanced color palette with gradients and semantic colors.
 * Includes colorblind-friendly alternatives.
 */
export const chartColorPalette = {
  primary: {
    solid: '#2563EB',
    gradient: ['#2563EB', '#3B82F6'],
    light: '#60A5FA',
    dark: '#1E40AF',
    pattern: 'solid' // For colorblind users
  },
  secondary: {
    solid: '#3B82F6',
    gradient: ['#3B82F6', '#60A5FA'],
    light: '#93C5FD',
    dark: '#2563EB',
    pattern: 'dashed'
  },
  success: {
    solid: '#16a34a',
    gradient: ['#16a34a', '#22c55e'],
    light: '#4ade80',
    dark: '#15803d',
    pattern: 'dotted'
  },
  warning: {
    solid: '#d97706',
    gradient: ['#d97706', '#f59e0b'],
    light: '#fbbf24',
    dark: '#b45309',
    pattern: 'dashed'
  },
  error: {
    solid: '#dc2626',
    gradient: ['#dc2626', '#ef4444'],
    light: '#f87171',
    dark: '#b91c1c',
    pattern: 'dotted'
  },
  info: {
    solid: '#4b5563',
    gradient: ['#4b5563', '#6b7280'],
    light: '#9ca3af',
    dark: '#374151',
    pattern: 'solid'
  },
  cta: {
    solid: '#F97316',
    gradient: ['#F97316', '#fb923c'],
    light: '#fdba74',
    dark: '#ea580c',
    pattern: 'dashed'
  }
}

/**
 * Create gradient fill for charts.
 * 
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {string} color1 - Start color (hex)
 * @param {string} color2 - End color (hex)
 * @param {number} opacity - Opacity (0-1, default: 0.2 for area charts)
 * @returns {CanvasGradient} Gradient object
 */
export function createGradient(ctx, color1, color2, opacity = 0.2) {
  if (!ctx || !ctx.canvas) {
    return color1 // Fallback to solid color if no canvas
  }
  
  const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
  
  // Convert hex to rgba
  const hexToRgba = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }
  
  gradient.addColorStop(0, hexToRgba(color1, opacity))
  gradient.addColorStop(1, hexToRgba(color2, opacity * 0.3))
  
  return gradient
}

/**
 * Convert hex color to rgba with opacity.
 * 
 * @param {string} hex - Hex color (#RRGGBB)
 * @param {number} opacity - Opacity (0-1)
 * @returns {string} RGBA color string
 */
export function hexToRgba(hex, opacity = 1) {
  if (!hex || !hex.startsWith('#')) {
    return hex // Return as-is if not hex
  }
  
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}

/**
 * Get colorblind-friendly pattern for line charts.
 * 
 * @param {string} colorKey - Color key from chartColorPalette
 * @returns {object} Chart.js line pattern config
 */
export function getColorblindPattern(colorKey) {
  const palette = chartColorPalette[colorKey] || chartColorPalette.primary
  const patterns = {
    solid: { borderDash: [] },
    dashed: { borderDash: [5, 5] },
    dotted: { borderDash: [2, 2] }
  }
  return patterns[palette.pattern] || patterns.solid
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
 * Animation configuration for charts.
 * Provides smooth entry animations and transitions.
 */
export const animationConfig = {
  duration: 800,
  easing: 'easeInOutQuart',
  delay: (context) => {
    // Stagger animation for multiple datasets
    return context.dataIndex * 50
  },
  // Progressive animation for line/area charts
  progressive: {
    duration: 1000,
    easing: 'easeOutQuart'
  }
}

/**
 * Get responsive chart height based on screen size.
 * 
 * @param {string} defaultHeight - Default height (e.g., '300px')
 * @returns {string} Responsive height
 */
export function getResponsiveChartHeight(defaultHeight = '300px') {
  if (typeof window === 'undefined') {
    return defaultHeight
  }
  
  const isMobile = window.innerWidth < 768
  const isTablet = window.innerWidth >= 768 && window.innerWidth < 1024
  
  if (isMobile) {
    return '200px'
  } else if (isTablet) {
    return '250px'
  }
  return defaultHeight || '300px'
}

/**
 * Get responsive chart options based on screen size.
 */
export function getResponsiveChartOptions(customOptions = {}) {
  // Check if we're in browser environment
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768
  const isTablet = typeof window !== 'undefined' && window.innerWidth >= 768 && window.innerWidth < 1024
  
  // Responsive font sizes
  const fontSize = isMobile ? 11 : isTablet ? 12 : 13
  const titleFontSize = isMobile ? 12 : isTablet ? 13 : 14
  const legendFontSize = isMobile ? 10 : isTablet ? 11 : 12
  
  // Merge with custom options, preserving custom plugins
  const mergedPlugins = {
    legend: {
      display: true,
      position: isMobile ? 'bottom' : 'top',
      labels: {
        usePointStyle: true,
        padding: isMobile ? 10 : 15,
        boxWidth: isMobile ? 10 : 12,
        boxHeight: isMobile ? 10 : 12,
        font: {
          family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: legendFontSize,
          weight: '500'
        },
        color: chartColors.gray[700]
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
    animation: {
      ...animationConfig,
      ...(customOptions.animation || {})
    },
    plugins: mergedPlugins,
    ...customOptions,
    // Override plugins with merged version
    plugins: mergedPlugins
  }
}

/**
 * Default chart options matching design system.
 * Enhanced with better typography, spacing, and visual elements.
 */
export const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: animationConfig,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 15,
        boxWidth: 12,
        boxHeight: 12,
        font: {
          family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 12,
          weight: '500'
        },
        color: chartColors.gray[700]
      },
      onClick: (e, legendItem, legend) => {
        // Toggle dataset visibility on legend click
        const index = legendItem.datasetIndex
        const chart = legend.chart
        const meta = chart.getDatasetMeta(index)
        meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null
        chart.update()
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      padding: 12,
      titleFont: {
        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 13,
        weight: 'bold'
      },
      bodyFont: {
        family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        size: 12,
        weight: 'normal'
      },
      borderColor: chartColors.gray[200],
      borderWidth: 1,
      cornerRadius: 8,
      displayColors: true,
      boxPadding: 6,
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
          // Format numbers with thousands separators
          const formattedValue = typeof value === 'number' 
            ? new Intl.NumberFormat('vi-VN').format(value)
            : value
          return `${label}: ${formattedValue}`
        },
        labelColor: (context) => {
          return {
            borderColor: context.dataset.borderColor || context.dataset.backgroundColor,
            backgroundColor: context.dataset.backgroundColor || context.dataset.borderColor
          }
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: true,
        color: chartColors.gray[100],
        lineWidth: 1,
        drawBorder: false
      },
      ticks: {
        font: {
          family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 11,
          weight: 'normal'
        },
        color: chartColors.gray[600],
        padding: 8
      }
    },
    y: {
      grid: {
        color: chartColors.gray[100],
        lineWidth: 1,
        drawBorder: false,
        drawOnChartArea: true
      },
      ticks: {
        font: {
          family: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          size: 11,
          weight: 'normal'
        },
        color: chartColors.gray[600],
        padding: 8,
        callback: function(value) {
          // Format large numbers with K, M suffixes
          if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M'
          }
          if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K'
          }
          return value
        }
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
