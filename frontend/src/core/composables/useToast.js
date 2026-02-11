/**
 * Toast notification composable.
 * 
 * Provides a simple API for showing toast notifications.
 * 
 * Usage:
 *   const toast = useToast()
 *   toast.success('Operation completed')
 *   toast.error('Something went wrong')
 *   toast.warning('Please check your input')
 *   toast.info('Processing...')
 */

import { ref } from 'vue'

// Global toast state
const toasts = ref([])
let toastIdCounter = 0

/**
 * Generate unique toast ID.
 * 
 * @returns {string} Unique toast ID
 */
const generateToastId = () => {
  return `toast-${Date.now()}-${++toastIdCounter}`
}

/**
 * Add toast to the queue.
 * 
 * @param {Object} toast - Toast configuration
 * @param {string} toast.type - Toast type (success, error, warning, info)
 * @param {string} toast.message - Toast message
 * @param {string} [toast.title] - Optional title
 * @param {number} [toast.duration] - Auto-dismiss duration in ms (default: 5000)
 * @returns {string} Toast ID
 */
const addToast = (toast) => {
  const id = generateToastId()
  const toastConfig = {
    id,
    type: toast.type,
    message: toast.message,
    title: toast.title || null,
    duration: toast.duration !== undefined ? toast.duration : 5000
  }
  
  toasts.value.push(toastConfig)
  
  // Limit to 5 toasts max
  if (toasts.value.length > 5) {
    toasts.value.shift()
  }
  
  return id
}

/**
 * Remove toast by ID.
 * 
 * @param {string} id - Toast ID
 */
const removeToast = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

/**
 * Toast composable.
 * 
 * @returns {Object} Toast methods
 */
export function useToast() {
  return {
    /**
     * Show success toast.
     * 
     * @param {string} message - Toast message
     * @param {string} [title] - Optional title
     * @param {Object} [options] - Options
     * @param {number} [options.duration] - Duration in ms
     * @returns {string} Toast ID
     */
    success: (message, title = null, options = {}) => {
      return addToast({
        type: 'success',
        message,
        title,
        duration: options.duration
      })
    },

    /**
     * Show error toast.
     * 
     * @param {string} message - Toast message
     * @param {string} [title] - Optional title
     * @param {Object} [options] - Options
     * @param {number} [options.duration] - Duration in ms
     * @returns {string} Toast ID
     */
    error: (message, title = null, options = {}) => {
      return addToast({
        type: 'error',
        message,
        title,
        duration: options.duration || 7000 // Errors stay longer
      })
    },

    /**
     * Show warning toast.
     * 
     * @param {string} message - Toast message
     * @param {string} [title] - Optional title
     * @param {Object} [options] - Options
     * @param {number} [options.duration] - Duration in ms
     * @returns {string} Toast ID
     */
    warning: (message, title = null, options = {}) => {
      return addToast({
        type: 'warning',
        message,
        title,
        duration: options.duration
      })
    },

    /**
     * Show info toast.
     * 
     * @param {string} message - Toast message
     * @param {string} [title] - Optional title
     * @param {Object} [options] - Options
     * @param {number} [options.duration] - Duration in ms
     * @returns {string} Toast ID
     */
    info: (message, title = null, options = {}) => {
      return addToast({
        type: 'info',
        message,
        title,
        duration: options.duration
      })
    },

    /**
     * Remove toast by ID.
     * 
     * @param {string} id - Toast ID
     */
    remove: removeToast
  }
}

// Export toast state for ToastContainer to use
export { toasts }
