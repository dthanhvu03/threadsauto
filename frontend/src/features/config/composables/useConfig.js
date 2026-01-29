/**
 * Config composable.
 * 
 * Provides business logic for configuration management.
 */

import { computed, ref } from 'vue'
import { useConfigStore } from '@/stores/config'
import { configService } from '../services/configService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for config feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useConfig() {
  const store = useConfigStore()
  const loading = ref(false)
  const error = ref(null)
  const saveSuccess = ref(false)

  /**
   * Fetch configuration.
   * 
   * @returns {Promise<Object|null>} Config object or null on error
   */
  const fetchConfig = async () => {
    loading.value = true
    error.value = null

    try {
      const config = await configService.get()
      store.setConfig(config)
      return config
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Update configuration.
   * 
   * @param {Object} configData - Configuration data to update
   * @returns {Promise<boolean>} True if successful, false otherwise
   */
  const updateConfig = async (configData) => {
    loading.value = true
    error.value = null
    saveSuccess.value = false

    try {
      const result = await configService.update(configData)
      
      // Deep merge config data
      const mergedConfig = deepMerge(store.config || {}, result || configData)
      store.setConfig(mergedConfig)
      saveSuccess.value = true
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        saveSuccess.value = false
      }, 3000)
      
      return true
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Deep merge two objects.
   * 
   * @param {Object} target - Target object
   * @param {Object} source - Source object
   * @returns {Object} Merged object
   */
  const deepMerge = (target, source) => {
    const output = { ...target }
    if (isObject(target) && isObject(source)) {
      Object.keys(source).forEach(key => {
        if (isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] })
          } else {
            output[key] = deepMerge(target[key], source[key])
          }
        } else {
          Object.assign(output, { [key]: source[key] })
        }
      })
    }
    return output
  }

  /**
   * Check if value is an object.
   * 
   * @param {*} item - Value to check
   * @returns {boolean} True if object
   */
  const isObject = (item) => {
    return item && typeof item === 'object' && !Array.isArray(item)
  }

  /**
   * Clear error.
   */
  const clearError = () => {
    error.value = null
    store.setError(null)
  }

  /**
   * Clear success message.
   */
  const clearSuccess = () => {
    saveSuccess.value = false
  }

  return {
    config: computed(() => store.config),
    loading,
    error,
    saveSuccess,
    fetchConfig,
    updateConfig,
    clearError,
    clearSuccess
  }
}
