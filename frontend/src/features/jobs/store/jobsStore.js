/**
 * Jobs store - state management only.
 * 
 * Business logic is in useJobs composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

/**
 * Jobs store.
 * 
 * @returns {Object} Pinia store
 */
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
     * 
     * @param {Job[]} jobs - Jobs array
     */
    setJobs(jobs) {
      this.jobs = jobs
    },

    /**
     * Set selected job.
     * 
     * @param {Job|null} job - Selected job
     */
    setSelectedJob(job) {
      this.selectedJob = job
    },

    /**
     * Remove job by ID.
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
     * 
     * @param {string|null} error - Error message
     */
    setError(error) {
      this.error = error
    },

    /**
     * Set filters.
     * 
     * @param {JobFilters} filters - Filter values
     */
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    /**
     * Clear filters.
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
