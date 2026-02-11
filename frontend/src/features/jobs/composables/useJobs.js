/**
 * Jobs composable.
 * 
 * Provides business logic and state management for jobs feature.
 * Combines service calls with store state management.
 */

import { computed, ref } from 'vue'
import { useJobsStore } from '../store/jobsStore'
import { jobsService } from '../services/jobsService'
import { ApiError } from '@/core/api/types'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for jobs feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useJobs() {
  const store = useJobsStore()
  const loading = ref(false)
  const error = ref(null)
  
  // Pagination state
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  /**
   * Fetch all jobs with optional filters and pagination.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.accountId] - Filter by account ID
   * @param {string} [options.status] - Filter by status
   * @param {string} [options.platform] - Filter by platform
   * @param {string} [options.scheduled_from] - Filter by scheduled from date (YYYY-MM-DD)
   * @param {string} [options.scheduled_to] - Filter by scheduled to date (YYYY-MM-DD)
   * @param {number} [options.page] - Page number (1-based)
   * @param {number} [options.limit] - Items per page
   * @param {boolean} [options.reload] - Reload jobs from storage
   * @returns {Promise<Job[]>}
   */
  const fetchJobs = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      // Use provided page/limit or current pagination state
      const page = options.page !== undefined ? options.page : currentPage.value
      const limit = options.limit !== undefined ? options.limit : pageSize.value
      
      // Build filter params - simplified logic
      // Use options if provided, otherwise use store filters, otherwise null
      const getFilterValue = (optionValue, storeValue) => {
        if (optionValue !== undefined && optionValue !== null && optionValue !== '') {
          return optionValue
        }
        if (storeValue !== undefined && storeValue !== null && storeValue !== '') {
          return storeValue
        }
        return null
      }
      
      const params = {
        account_id: getFilterValue(options.accountId, store.filters.accountId),
        status: getFilterValue(options.status, store.filters.status),
        platform: getFilterValue(options.platform, store.filters.platform),
        scheduled_from: getFilterValue(options.scheduled_from, store.filters.scheduled_from),
        scheduled_to: getFilterValue(options.scheduled_to, store.filters.scheduled_to),
        page: page,
        limit: limit
      }
      
      // Add reload if requested
      if (options.reload) {
        params.reload = true
      }
      
      // Remove null/empty values
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === '') {
          delete params[key]
        }
      })
      
      // Call API - response will be data array with _pagination attached by API client
      const response = await jobsService.getAll(params)
      
      // API client interceptor returns:
      // - For arrays with pagination: {data: [], _pagination: {}}
      // - For objects: object with _pagination attached
      // - For arrays without pagination: array
      let jobs = []
      let pagination = null
      
      if (response && typeof response === 'object') {
        // Check if response has data property (from API client for paginated arrays)
        if (Array.isArray(response.data)) {
          jobs = response.data
          pagination = response._pagination || null
        } 
        // Check if response is array (no pagination)
        else if (Array.isArray(response)) {
          jobs = response
          pagination = null
        }
        // Check if response has _pagination attached (for object responses)
        else if (response._pagination) {
          // Response is object with _pagination
          jobs = Array.isArray(response) ? response : []
          pagination = response._pagination
        }
        // Fallback: treat as array if it's array-like
        else if (Array.isArray(response)) {
          jobs = response
        }
      } else if (Array.isArray(response)) {
        // Response is plain array
        jobs = response
        pagination = null
      }
      
      // Update pagination state
      if (pagination) {
        currentPage.value = pagination.page || page
        pageSize.value = pagination.limit || limit
        total.value = pagination.total || 0
      } else if (page && limit) {
        // Pagination was requested but no metadata returned - this is an error
        // Use jobs length as fallback
        currentPage.value = page
        pageSize.value = limit
        total.value = jobs.length
      } else {
        // No pagination requested - use jobs length
        total.value = jobs.length
      }
      
      store.setJobs(jobs)
      return jobs
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
   * Fetch job by ID.
   * 
   * @param {string} jobId - Job ID
   * @returns {Promise<Job|null>}
   */
  const fetchJobById = async (jobId) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const job = await jobsService.getById(jobId)
      store.setSelectedJob(job)
      return job
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
   * Create new job.
   * 
   * Business logic: Formats job data (platform/priority to uppercase, sets scheduled_time if not provided)
   * 
   * @param {JobCreateData} jobData - Job creation data
   * @returns {Promise<Job|null>}
   */
  const createJob = async (jobData) => {
    loading.value = true
    error.value = null

    try {
      // Business logic: Format job data
      const formattedJobData = {
        ...jobData,
        platform: jobData.platform?.toUpperCase() || 'THREADS',
        priority: jobData.priority?.toUpperCase() || 'NORMAL'
      }
      
      // Business logic: Set scheduled_time if not provided (default: 1 hour from now)
      if (!formattedJobData.scheduled_time) {
        const oneHourLater = new Date()
        oneHourLater.setHours(oneHourLater.getHours() + 1)
        formattedJobData.scheduled_time = oneHourLater.toISOString()
      }
      
      // API client already extracts data from success response
      const result = await jobsService.create(formattedJobData)
      // Refresh jobs list - preserve all current filters (status, platform, dates, etc.)
      await fetchJobs({ 
        accountId: store.filters.accountId,
        status: store.filters.status,
        platform: store.filters.platform,
        scheduled_from: store.filters.scheduled_from,
        scheduled_to: store.filters.scheduled_to,
        page: currentPage.value,
        limit: pageSize.value,
        reload: true  // Force reload to get newly created job
      })
      return result
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
   * Update job.
   * 
   * @param {string} jobId - Job ID
   * @param {JobUpdateData} jobData - Updated job data
   * @returns {Promise<Job|null>}
   */
  const updateJob = async (jobId, jobData) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const result = await jobsService.update(jobId, jobData)
      // Refresh jobs list - preserve all current filters
      await fetchJobs({ 
        accountId: store.filters.accountId,
        status: store.filters.status,
        platform: store.filters.platform,
        scheduled_from: store.filters.scheduled_from,
        scheduled_to: store.filters.scheduled_to,
        page: currentPage.value,
        limit: pageSize.value,
        reload: false  // Changed from true to false
      })
      return result
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
   * Delete job.
   * 
   * @param {string} jobId - Job ID
   * @returns {Promise<boolean>}
   */
  const deleteJob = async (jobId) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      await jobsService.delete(jobId)
      // Remove from local state
      store.removeJob(jobId)
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
   * Get job statistics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<JobStats>}
   */
  const fetchStats = async (accountId = null) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const stats = await jobsService.getStats(accountId)
      return stats
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
   * Filtered jobs computed property.
   * 
   * Note: With pagination, most filtering is done on the backend.
   * This is kept for client-side filtering if needed.
   * 
   * @type {import('vue').ComputedRef<Job[]>}
   */
  const filteredJobs = computed(() => {
    // With pagination, jobs are already filtered on backend
    // Return jobs as-is, or apply additional client-side filters if needed
    return store.jobs
  })
  
  /**
   * Go to specific page.
   * 
   * @param {number} page - Page number (1-based)
   */
  const goToPage = async (page) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      // Preserve current filters when changing page
      await fetchJobs({ 
        page,
        accountId: store.filters.accountId,
        status: store.filters.status,
        platform: store.filters.platform,
        scheduled_from: store.filters.scheduled_from,
        scheduled_to: store.filters.scheduled_to
      })
    }
  }
  
  /**
   * Change page size.
   * 
   * @param {number} size - Items per page
   */
  const changePageSize = async (size) => {
    pageSize.value = size
    currentPage.value = 1 // Reset to first page
    // Preserve current filters when changing page size
    await fetchJobs({ 
      page: 1, 
      limit: size,
      accountId: store.filters.accountId,
      status: store.filters.status,
      platform: store.filters.platform,
      scheduled_from: store.filters.scheduled_from,
      scheduled_to: store.filters.scheduled_to
    })
  }

  /**
   * Jobs grouped by status.
   * 
   * @type {import('vue').ComputedRef<Object>}
   */
  const jobsByStatus = computed(() => {
    const grouped = {}
    store.jobs.forEach(job => {
      const status = job.status || 'unknown'
      grouped[status] = (grouped[status] || 0) + 1
    })
    return grouped
  })

  /**
   * Set filters.
   * 
   * @param {JobFilters} filters - Filter values
   */
  const setFilters = (filters) => {
    store.setFilters(filters)
  }

  /**
   * Clear filters.
   */
  const clearFilters = () => {
    store.clearFilters()
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
    jobs: computed(() => store.jobs),
    selectedJob: computed(() => store.selectedJob),
    filters: computed(() => store.filters),
    loading,
    error,
    // Pagination state
    currentPage: computed(() => currentPage.value),
    pageSize: computed(() => pageSize.value),
    total: computed(() => total.value),
    totalPages,
    // Computed
    filteredJobs,
    jobsByStatus,
    // Methods
    fetchJobs,
    fetchJobById,
    createJob,
    updateJob,
    deleteJob,
    fetchStats,
    setFilters,
    clearFilters,
    clearError,
    // Pagination methods
    goToPage,
    changePageSize
  }
}
