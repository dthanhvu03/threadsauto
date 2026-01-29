/**
 * Config store - State management only.
 * 
 * @deprecated This store is kept for backward compatibility.
 * New code should use the composable: @/features/config/composables/useConfig
 * 
 * Business logic is in useConfig composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

export const useConfigStore = defineStore('config', {
  state: () => ({
    config: null,
    error: null
  }),

  actions: {
    /**
     * Set config.
     * Called by useConfig composable.
     * 
     * @param {Object|null} config - Configuration object
     */
    setConfig(config) {
      this.config = config
    },

    /**
     * Set error.
     * Called by useConfig composable.
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
      this.config = null
      this.error = null
    }
  }
})
