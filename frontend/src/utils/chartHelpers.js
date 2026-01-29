/**
 * Chart helper utilities.
 * 
 * Provides common chart data transformations and formatting helpers.
 */

import { formatDateVN, formatDateTimeVN } from './datetime'
import { chartColors } from './chartConfig'

/**
 * Group data by date.
 * 
 * @param {Array} data - Array of items with date field
 * @param {string} dateKey - Key for date field (default: 'date')
 * @param {string} valueKey - Key for value field (default: 'value')
 * @returns {Object} Grouped data by date
 */
export function groupByDate(data, dateKey = 'date', valueKey = 'value') {
  const grouped = {}
  data.forEach(item => {
    const date = formatDateVN(item[dateKey])
    if (!grouped[date]) {
      grouped[date] = []
    }
    grouped[date].push(item[valueKey] || item)
  })
  return grouped
}

/**
 * Aggregate data by key.
 * 
 * @param {Array} data - Array of items
 * @param {string} key - Key to group by
 * @param {string} valueKey - Key for value to aggregate (default: 'value')
 * @returns {Object} Aggregated data
 */
export function aggregateByKey(data, key, valueKey = 'value') {
  const aggregated = {}
  data.forEach(item => {
    const k = item[key]
    aggregated[k] = (aggregated[k] || 0) + (item[valueKey] || 1)
  })
  return aggregated
}

/**
 * Create time series data from array of items.
 * 
 * @param {Array} items - Array of items with date and value
 * @param {string} dateKey - Key for date field
 * @param {string} valueKey - Key for value field
 * @param {Function} valueTransform - Optional transform function for values
 * @returns {Object} Chart data with labels and datasets
 */
export function createTimeSeries(items, dateKey = 'date', valueKey = 'value', valueTransform = null) {
  if (!items || items.length === 0) {
    return { labels: [], datasets: [] }
  }

  const sorted = [...items].sort((a, b) => {
    const dateA = new Date(a[dateKey])
    const dateB = new Date(b[dateKey])
    return dateA - dateB
  })

  const labels = sorted.map(item => formatDateVN(item[dateKey]))
  const values = sorted.map(item => {
    const value = item[valueKey] || 0
    return valueTransform ? valueTransform(value) : value
  })

  return {
    labels,
    datasets: [{
      label: valueKey,
      data: values,
      borderColor: chartColors.primary,
      backgroundColor: chartColors.primary + '20',
      fill: true,
      tension: 0.4
    }]
  }
}

/**
 * Create comparison chart data (two series).
 * 
 * @param {Array} items - Array of items
 * @param {string} dateKey - Key for date field
 * @param {string} series1Key - Key for first series
 * @param {string} series2Key - Key for second series
 * @param {string} series1Label - Label for first series
 * @param {string} series2Label - Label for second series
 * @returns {Object} Chart data with labels and datasets
 */
export function createComparisonChart(
  items,
  dateKey = 'date',
  series1Key,
  series2Key,
  series1Label = 'Series 1',
  series2Label = 'Series 2'
) {
  if (!items || items.length === 0) {
    return { labels: [], datasets: [] }
  }

  const sorted = [...items].sort((a, b) => {
    const dateA = new Date(a[dateKey])
    const dateB = new Date(b[dateKey])
    return dateA - dateB
  })

  const labels = sorted.map(item => formatDateVN(item[dateKey]))
  const series1Data = sorted.map(item => item[series1Key] || 0)
  const series2Data = sorted.map(item => item[series2Key] || 0)

  return {
    labels,
    datasets: [
      {
        label: series1Label,
        data: series1Data,
        backgroundColor: chartColors.primary + '80',
        borderColor: chartColors.primary
      },
      {
        label: series2Label,
        data: series2Data,
        backgroundColor: chartColors.secondary + '80',
        borderColor: chartColors.secondary
      }
    ]
  }
}

/**
 * Create histogram data from array of values.
 * 
 * @param {Array} values - Array of numeric values
 * @param {Array} buckets - Array of bucket boundaries
 * @param {Array} bucketLabels - Array of labels for buckets
 * @returns {Object} Chart data with labels and datasets
 */
export function createHistogram(values, buckets, bucketLabels) {
  if (!values || values.length === 0) {
    return { labels: [], datasets: [] }
  }

  const bucketCounts = new Array(buckets.length).fill(0)
  values.forEach(value => {
    for (let i = 0; i < buckets.length; i++) {
      if (i === buckets.length - 1 || value < buckets[i + 1]) {
        bucketCounts[i]++
        break
      }
    }
  })

  return {
    labels: bucketLabels,
    datasets: [{
      label: 'Frequency',
      data: bucketCounts,
      backgroundColor: chartColors.primary + '80',
      borderColor: chartColors.primary,
      borderWidth: 1
    }]
  }
}

/**
 * Format tooltip value.
 * 
 * @param {*} value - Value to format
 * @param {string} format - Format type ('number', 'percentage', 'currency', 'duration')
 * @returns {string} Formatted value
 */
export function formatTooltipValue(value, format = 'number') {
  if (value === null || value === undefined) return 'N/A'
  
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  
  switch (format) {
    case 'percentage':
      return `${numValue.toFixed(1)}%`
    case 'currency':
      return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(numValue)
    case 'duration':
      if (numValue < 60) return `${numValue.toFixed(1)}s`
      if (numValue < 3600) return `${Math.floor(numValue / 60)}m ${(numValue % 60).toFixed(0)}s`
      return `${Math.floor(numValue / 3600)}h ${Math.floor((numValue % 3600) / 60)}m`
    default:
      return new Intl.NumberFormat('vi-VN').format(numValue)
  }
}

/**
 * Format chart label (date/time).
 * 
 * @param {string|Date} date - Date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted label
 */
export function formatChartLabel(date, includeTime = false) {
  if (!date) return ''
  return includeTime ? formatDateTimeVN(date) : formatDateVN(date)
}
