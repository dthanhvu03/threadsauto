/**
 * Composable for lazy loading charts.
 * Only renders charts when they enter the viewport.
 */

import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable for lazy loading chart components.
 * 
 * @returns {Object} Lazy loading utilities
 */
export function useLazyChart() {
  const isVisible = ref(false)
  const chartRef = ref(null)

  const observer = ref(null)

  onMounted(() => {
    if (typeof IntersectionObserver === 'undefined') {
      // Fallback for browsers without IntersectionObserver
      isVisible.value = true
      return
    }

    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            isVisible.value = true
            // Stop observing once visible
            if (observer.value && chartRef.value) {
              observer.value.unobserve(chartRef.value)
            }
          }
        })
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.1
      }
    )

    if (chartRef.value) {
      observer.value.observe(chartRef.value)
    }
  })

  onUnmounted(() => {
    if (observer.value && chartRef.value) {
      observer.value.unobserve(chartRef.value)
      observer.value.disconnect()
    }
  })

  return {
    isVisible,
    chartRef
  }
}
