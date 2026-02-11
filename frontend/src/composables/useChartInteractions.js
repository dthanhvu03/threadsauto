/**
 * Composable for chart interactions.
 * Provides utilities for chart export, zoom, pan, and other interactions.
 */

import { ref } from 'vue'

/**
 * Export chart as image.
 * 
 * @param {HTMLCanvasElement} canvas - Chart canvas element
 * @param {string} filename - Filename for download
 * @param {string} format - Image format ('png' or 'jpeg')
 */
export function exportChart(canvas, filename = 'chart', format = 'png') {
  if (!canvas) {
    console.error('Canvas element not found')
    return
  }

  try {
    const url = canvas.toDataURL(`image/${format}`, 1.0)
    const link = document.createElement('a')
    link.download = `${filename}.${format}`
    link.href = url
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    console.error('Error exporting chart:', error)
  }
}

/**
 * Get chart canvas element from chart instance.
 * 
 * @param {Object} chartInstance - Chart.js chart instance
 * @returns {HTMLCanvasElement|null} Canvas element
 */
export function getChartCanvas(chartInstance) {
  if (!chartInstance || !chartInstance.canvas) {
    return null
  }
  return chartInstance.canvas
}

/**
 * Composable for managing chart interactions.
 * 
 * @returns {Object} Chart interaction utilities
 */
export function useChartInteractions() {
  const isExporting = ref(false)

  /**
   * Export chart as PNG.
   * 
   * @param {Object} chartInstance - Chart.js chart instance
   * @param {string} filename - Filename for download
   */
  const exportAsPNG = (chartInstance, filename = 'chart') => {
    const canvas = getChartCanvas(chartInstance)
    if (!canvas) return

    isExporting.value = true
    try {
      exportChart(canvas, filename, 'png')
    } finally {
      setTimeout(() => {
        isExporting.value = false
      }, 500)
    }
  }

  /**
   * Export chart as JPEG.
   * 
   * @param {Object} chartInstance - Chart.js chart instance
   * @param {string} filename - Filename for download
   */
  const exportAsJPEG = (chartInstance, filename = 'chart') => {
    const canvas = getChartCanvas(chartInstance)
    if (!canvas) return

    isExporting.value = true
    try {
      exportChart(canvas, filename, 'jpeg')
    } finally {
      setTimeout(() => {
        isExporting.value = false
      }, 500)
    }
  }

  /**
   * Copy chart to clipboard.
   * 
   * @param {Object} chartInstance - Chart.js chart instance
   */
  const copyToClipboard = async (chartInstance) => {
    const canvas = getChartCanvas(chartInstance)
    if (!canvas) return

    try {
      const blob = await new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png')
      })
      
      if (blob) {
        await navigator.clipboard.write([
          new ClipboardItem({ 'image/png': blob })
        ])
      }
    } catch (error) {
      console.error('Error copying chart to clipboard:', error)
    }
  }

  return {
    isExporting,
    exportAsPNG,
    exportAsJPEG,
    copyToClipboard,
    getChartCanvas
  }
}
