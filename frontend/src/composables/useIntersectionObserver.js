/**
 * IntersectionObserver composable for lazy loading.
 * 
 * Provides reactive intersection state for elements entering/exiting viewport.
 * Automatically cleans up observer on component unmount.
 */

import { ref, onMounted, onUnmounted, watch } from 'vue'

/**
 * Use IntersectionObserver to track element visibility.
 * 
 * @param {Object} options - IntersectionObserver options
 * @param {string} options.rootMargin - Margin around root (e.g., '50px')
 * @param {number|Array<number>} options.threshold - Intersection threshold (0-1)
 * @param {Element} options.root - Root element (default: null = viewport)
 * @param {boolean} options.once - Unobserve after first intersection (default: true)
 * @returns {Object} { isIntersecting, element, observe, unobserve }
 */
export function useIntersectionObserver(options = {}) {
  const {
    rootMargin = '50px',
    threshold = 0.1,
    root = null,
    once = true
  } = options

  const isIntersecting = ref(false)
  const element = ref(null)
  let observer = null

  /**
   * Create and start observing element.
   */
  const observe = (el) => {
    if (!el) return

    // Unobserve previous element if exists
    if (element.value && observer) {
      observer.unobserve(element.value)
    }

    element.value = el

    // Create observer if not exists
    if (!observer) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            isIntersecting.value = entry.isIntersecting

            // If once=true, unobserve after first intersection
            if (once && entry.isIntersecting && observer) {
              observer.unobserve(entry.target)
            }
          })
        },
        {
          root,
          rootMargin,
          threshold
        }
      )
    }

    // Start observing
    observer.observe(el)
  }

  /**
   * Stop observing element.
   */
  const unobserve = () => {
    if (observer && element.value) {
      observer.unobserve(element.value)
      element.value = null
    }
  }

  /**
   * Cleanup observer.
   */
  const disconnect = () => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
    element.value = null
    isIntersecting.value = false
  }

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isIntersecting,
    element,
    observe,
    unobserve,
    disconnect
  }
}
