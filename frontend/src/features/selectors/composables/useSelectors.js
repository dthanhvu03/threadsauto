/**
 * Selectors composable.
 * 
 * Provides business logic for selector management.
 */

import { computed, ref } from 'vue'
import { useSelectorsStore } from '@/stores/selectors'
import { selectorsService } from '../services/selectorsService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for selectors feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useSelectors() {
  const store = useSelectorsStore()
  const loading = ref(false)
  const error = ref(null)
  const saveSuccess = ref(false)

  /**
   * Fetch selectors for platform and version.
   * 
   * @param {string} [version] - Selector version
   * @param {string} [platform] - Platform name
   * @returns {Promise<Object|null>} Selectors object or null on error
   */
  const fetchSelectors = async (version = null, platform = null) => {
    loading.value = true
    error.value = null

    try {
      const platformToUse = platform || store.currentPlatform
      const versionToUse = version || store.currentVersion
      
      const data = await selectorsService.get(versionToUse, platformToUse)
      const selectors = data?.selectors || data
      
      store.setSelectors(selectors)
      if (version) {
        store.setVersion(version)
      }
      if (platform) {
        store.setPlatform(platform)
      }
      
      return selectors
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
   * Update selectors.
   * 
   * @param {Object} selectorsData - Selectors data to update
   * @returns {Promise<boolean>} True if successful, false otherwise
   */
  const updateSelectors = async (selectorsData) => {
    loading.value = true
    error.value = null
    saveSuccess.value = false

    try {
      // Ensure platform is included
      if (!selectorsData.platform) {
        selectorsData.platform = store.currentPlatform
      }
      
      const result = await selectorsService.update(selectorsData)
      
      store.setSelectors(result?.selectors || result)
      if (result?.version) {
        store.setVersion(result.version)
      }
      if (result?.platform) {
        store.setPlatform(result.platform)
      }
      
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
   * Fetch available versions for platform.
   * 
   * @param {string} [platform] - Platform name
   * @returns {Promise<string[]>} Array of version strings
   */
  const fetchVersions = async (platform = null) => {
    try {
      const platformToUse = platform || store.currentPlatform
      const data = await selectorsService.getVersions(platformToUse)
      const versions = data?.versions || (Array.isArray(data) ? data : [])
      
      store.setAvailableVersions(versions)
      return versions
    } catch (err) {
      console.error('Error fetching versions:', err)
      return []
    }
  }

  /**
   * Set version and fetch selectors.
   * 
   * @param {string} version - Version to set
   */
  const setVersion = async (version) => {
    store.setVersion(version)
    await fetchSelectors(version, store.currentPlatform)
  }

  /**
   * Set platform and fetch selectors.
   * 
   * @param {string} platform - Platform to set
   */
  const setPlatform = async (platform) => {
    store.setPlatform(platform)
    await fetchSelectors(store.currentVersion, platform)
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
    selectors: computed(() => store.selectors),
    currentVersion: computed(() => store.currentVersion),
    currentPlatform: computed(() => store.currentPlatform),
    availableVersions: computed(() => store.availableVersions),
    loading,
    error,
    saveSuccess,
    fetchSelectors,
    updateSelectors,
    fetchVersions,
    setVersion,
    setPlatform,
    clearError,
    clearSuccess
  }
}
