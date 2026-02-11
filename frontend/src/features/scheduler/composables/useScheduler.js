/**
 * Scheduler composable.
 * 
 * Provides business logic and state management for scheduler feature.
 * Combines service calls with store state management.
 */

import { computed, ref } from 'vue'
import { useSchedulerStore } from '../store/schedulerStore'
import { schedulerService } from '../services/schedulerService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for scheduler feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useScheduler() {
  const store = useSchedulerStore()
  const loading = ref(false)
  const error = ref(null)

  /**
   * Fetch scheduler status.
   * 
   * @returns {Promise<SchedulerStatus>}
   */
  const fetchStatus = async () => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const status = await schedulerService.getStatus()
      
      // Map snake_case from API to camelCase for frontend
      const mappedStatus = status ? {
        running: status.running,
        activeJobsCount: status.active_jobs_count ?? status.activeJobsCount ?? 0
      } : { running: false, activeJobsCount: 0 }
      
      store.setStatus(mappedStatus)
      
      return status
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch active jobs.
   * 
   * @returns {Promise<Job[]>}
   */
  const fetchActiveJobs = async () => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      // But when meta is present, it returns {data: [...], _meta: {...}} instead of array
      const response = await schedulerService.getActiveJobs()
      
      // Handle both array and wrapped response formats
      let jobsArray = []
      if (Array.isArray(response)) {
        jobsArray = response
      } else if (response && Array.isArray(response.data)) {
        jobsArray = response.data
      }
      
      store.setActiveJobs(jobsArray)
      
      return jobsArray
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Start scheduler.
   * 
   * @param {string} [accountId] - Optional account ID
   * @returns {Promise<boolean>}
   */
  const start = async (accountId = null) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      await schedulerService.start(accountId)
      // Refresh status after starting
      await fetchStatus()
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
   * Stop scheduler.
   * 
   * @returns {Promise<boolean>}
   */
  const stop = async () => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      await schedulerService.stop()
      // Refresh status after stopping
      await fetchStatus()
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
   * Refresh all scheduler data.
   * 
   * @returns {Promise<void>}
   */
  const refresh = async () => {
    await Promise.all([
      fetchStatus(),
      fetchActiveJobs()
    ])
  }

  /**
   * Clear error.
   */
  const clearError = () => {
    error.value = null
    store.setError(null)
  }

  return {
    // State
    status: computed(() => store.status),
    activeJobs: computed(() => store.activeJobs),
    loading,
    error,
    // Methods
    fetchStatus,
    fetchActiveJobs,
    start,
    stop,
    refresh,
    clearError
  }
}
