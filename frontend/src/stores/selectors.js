/**
 * Selectors store - State management only.
 * 
 * @deprecated This store is kept for backward compatibility.
 * New code should use the composable: @/features/selectors/composables/useSelectors
 * 
 * Business logic is in useSelectors composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

export const useSelectorsStore = defineStore('selectors', {
  state: () => ({
    selectors: null,
    currentVersion: 'v1',
    currentPlatform: 'threads',
    availableVersions: [],
    error: null
  }),

  actions: {
    /**
     * Set selectors.
     * Called by useSelectors composable.
     * 
     * @param {Object|null} selectors - Selectors object
     */
    setSelectors(selectors) {
      this.selectors = selectors
    },

    /**
     * Set current version.
     * Called by useSelectors composable.
     * 
     * @param {string} version - Version string
     */
    setVersion(version) {
      this.currentVersion = version
    },

    /**
     * Set current platform.
     * Called by useSelectors composable.
     * 
     * @param {string} platform - Platform name
     */
    setPlatform(platform) {
      this.currentPlatform = platform
    },

    /**
     * Set available versions.
     * Called by useSelectors composable.
     * 
     * @param {string[]} versions - Array of version strings
     */
    setAvailableVersions(versions) {
      this.availableVersions = versions
    },

    /**
     * Set error.
     * Called by useSelectors composable.
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
      this.selectors = null
      this.currentVersion = 'v1'
      this.currentPlatform = 'threads'
      this.availableVersions = []
      this.error = null
    }
  }
})
