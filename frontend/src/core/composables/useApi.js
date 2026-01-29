/**
 * Generic API composable.
 * 
 * Provides reactive state and methods for API calls.
 * Can be used as a base for feature-specific composables.
 */

import { ref, computed } from 'vue'
import { ApiError } from '../api/types'

/**
 * Generic API composable.
 * 
 * @param {Object} options - Options
 * @param {Function} options.apiCall - API call function
 * @param {*} [options.initialData] - Initial data value
 * @returns {Object} Composable return object
 */
export function useApi(options = {}) {
  const { apiCall, initialData = null } = options

  // State
  const data = ref(initialData)
  const loading = ref(false)
  const error = ref(null)

  /**
   * Execute API call.
   * 
   * @param {...*} args - Arguments to pass to apiCall
   * @returns {Promise<*>}
   */
  const execute = async (...args) => {
    loading.value = true
    error.value = null

    try {
      const result = await apiCall(...args)
      data.value = result
      return result
    } catch (err) {
      error.value = err instanceof ApiError ? err : new ApiError(
        'INTERNAL_ERROR',
        err.message || 'An error occurred',
        {},
        0
      )
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset state.
   */
  const reset = () => {
    data.value = initialData
    loading.value = false
    error.value = null
  }

  /**
   * Check if there is an error.
   * 
   * @type {import('vue').ComputedRef<boolean>}
   */
  const hasError = computed(() => error.value !== null)

  /**
   * Check if operation is successful.
   * 
   * @type {import('vue').ComputedRef<boolean>}
   */
  const isSuccess = computed(() => !loading.value && !error.value && data.value !== null)

  return {
    // State
    data,
    loading,
    error,
    // Computed
    hasError,
    isSuccess,
    // Methods
    execute,
    reset
  }
}

/**
 * Composable for list operations with pagination.
 * 
 * @param {Object} options - Options
 * @param {Function} options.fetchFn - Function to fetch data
 * @returns {Object} Composable return object
 */
export function useApiList(options = {}) {
  const { fetchFn } = options

  const {
    data: items,
    loading,
    error,
    execute,
    reset,
    hasError,
    isSuccess
  } = useApi({
    apiCall: fetchFn,
    initialData: []
  })

  /**
   * Refresh list.
   * 
   * @param {Object} [params] - Query parameters
   * @returns {Promise<*>}
   */
  const refresh = async (params = {}) => {
    return execute(params)
  }

  return {
    items,
    loading,
    error,
    refresh,
    reset,
    hasError,
    isSuccess
  }
}
