/**
 * Jobs store - State management only.
 * 
 * @deprecated This store is kept for backward compatibility.
 * New code should use the composable: @/features/jobs/composables/useJobs
 * 
 * Business logic is in useJobs composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

export const useJobsStore = defineStore('jobs', {
  state: () => ({
    jobs: [],
    selectedJob: null,
    error: null,
    filters: {
      accountId: null,
      status: null,
      platform: null,
      scheduled_from: null,
      scheduled_to: null
    }
  }),

  getters: {
    /**
     * Filtered jobs based on current filters.
     * 
     * @param {Object} state - Store state
     * @returns {Job[]} Filtered jobs array
     */
    filteredJobs: (state) => {
      let filtered = state.jobs

      if (state.filters.accountId) {
        filtered = filtered.filter(job => job.account_id === state.filters.accountId)
      }

      if (state.filters.status) {
        filtered = filtered.filter(job => job.status === state.filters.status)
      }

      if (state.filters.platform) {
        filtered = filtered.filter(job => job.platform === state.filters.platform)
      }

      return filtered
    },

    /**
     * Jobs grouped by status.
     * 
     * @param {Object} state - Store state
     * @returns {Object} Jobs grouped by status
     */
    jobsByStatus: (state) => {
      const grouped = {}
      state.jobs.forEach(job => {
        const status = job.status || 'unknown'
        grouped[status] = (grouped[status] || 0) + 1
      })
      return grouped
    }
  },

  actions: {
    /**
     * Set jobs.
     * Called by useJobs composable.
     * 
     * @param {Job[]} jobs - Jobs array
     */
    setJobs(jobs) {
      this.jobs = jobs
    },

    /**
     * Set selected job.
     * Called by useJobs composable.
     * 
     * @param {Job|null} job - Selected job
     */
    setSelectedJob(job) {
      this.selectedJob = job
    },

    /**
     * Remove job by ID.
     * Called by useJobs composable.
     * 
     * @param {string} jobId - Job ID
     */
    removeJob(jobId) {
      this.jobs = this.jobs.filter(job => job.job_id !== jobId)
      if (this.selectedJob?.job_id === jobId) {
        this.selectedJob = null
      }
    },

    /**
     * Set error.
     * Called by useJobs composable.
     * 
     * @param {string|null} error - Error message
     */
    setError(error) {
      this.error = error
    },

    /**
     * Set filters.
     * Called by useJobs composable.
     * 
     * @param {JobFilters} filters - Filter values
     */
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * Clear filters.
     * Called by useJobs composable.
     */
    clearFilters() {
      this.filters = {
        accountId: null,
        status: null,
        platform: null,
        scheduled_from: null,
        scheduled_to: null
      }
    },

    /**
     * Reset store state.
     */
    reset() {
      this.jobs = []
      this.selectedJob = null
      this.error = null
      this.clearFilters()
    }
  }
})
