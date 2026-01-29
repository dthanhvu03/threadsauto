/**
 * Scheduler store - state management only.
 * 
 * Business logic is in useScheduler composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

/**
 * Scheduler store.
 * 
 * @returns {Object} Pinia store
 */
export const useSchedulerStore = defineStore('scheduler', {
  state: () => ({
    status: {
      running: false,
      activeJobsCount: 0
    },
    activeJobs: [],
    error: null
  }),

  actions: {
    /**
     * Set scheduler status.
     * 
     * @param {SchedulerStatus} status - Scheduler status
     */
    setStatus(status) {
      this.status = status
    },

    /**
     * Set active jobs.
     * 
     * @param {Job[]} jobs - Active jobs array
     */
    setActiveJobs(jobs) {
      this.activeJobs = jobs
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
     * Reset store state.
     */
    reset() {
      this.status = {
        running: false,
        activeJobsCount: 0
      }
      this.activeJobs = []
      this.error = null
    }
  }
})
