/**
 * Scheduler store - State management only.
 * 
 * @deprecated This store is kept for backward compatibility.
 * New code should use the composable: @/features/scheduler/composables/useScheduler
 * 
 * Business logic is in useScheduler composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

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
     * Called by useScheduler composable.
     * 
     * @param {SchedulerStatus} status - Scheduler status
     */
    setStatus(status) {
      this.status = status
    },

    /**
     * Set active jobs.
     * Called by useScheduler composable.
     * 
     * @param {Job[]} jobs - Active jobs array
     */
    setActiveJobs(jobs) {
      this.activeJobs = jobs
    },

    /**
     * Set error.
     * Called by useScheduler composable.
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
