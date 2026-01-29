/**
 * Dashboard store - state management only.
 * 
 * Business logic is in useDashboard composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

/**
 * Dashboard store.
 * 
 * @returns {Object} Pinia store
 */
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    stats: null,
    metrics: null,
    activity: [],
    error: null,
    lastUpdated: null
  }),

  getters: {
    /**
     * Check if data is stale (older than 1 minute).
     * 
     * @param {Object} state - Store state
     * @returns {boolean}
     */
    isStale: (state) => {
      if (!state.lastUpdated) return true
      const now = new Date()
      const lastUpdate = new Date(state.lastUpdated)
      const diff = now - lastUpdate
      return diff > 60000 // 1 minute
    }
  },

  actions: {
    /**
     * Set dashboard statistics.
     * 
     * @param {DashboardStats} stats - Dashboard statistics
     */
    setStats(stats) {
      this.stats = stats
      this.lastUpdated = new Date()
    },

    /**
     * Set dashboard metrics.
     * 
     * @param {DashboardMetrics} metrics - Dashboard metrics
     */
    setMetrics(metrics) {
      this.metrics = metrics
      this.lastUpdated = new Date()
    },

    /**
     * Set recent activity.
     * 
     * @param {Activity[]} activity - Recent activity array
     */
    setActivity(activity) {
      this.activity = activity
      this.lastUpdated = new Date()
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
      this.stats = null
      this.metrics = null
      this.activity = []
      this.error = null
      this.lastUpdated = null
    }
  }
})
