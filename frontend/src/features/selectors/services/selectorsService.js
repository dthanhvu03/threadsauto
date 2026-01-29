/**
 * Selectors API service.
 * 
 * Handles all API calls for selectors feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Selectors service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class SelectorsService extends BaseService {
  constructor() {
    super('/selectors')
  }

  /**
   * Get selectors.
   * 
   * @param {string} [version] - Selector version
   * @param {string} [platform] - Platform (threads, facebook)
   * @returns {Promise<Object>} API response with selectors data
   */
  async get(version = null, platform = null) {
    const params = {}
    if (version) params.version = version
    if (platform) params.platform = platform
    return super.get('', params)
  }

  /**
   * Update selectors.
   * 
   * @param {Object} selectorsData - Selectors data
   * @returns {Promise<Object>} API response with updated selectors
   */
  async update(selectorsData) {
    return this.put('', selectorsData)
  }

  /**
   * Get available versions.
   * 
   * @param {string} [platform] - Platform (threads, facebook)
   * @returns {Promise<Array>} API response with available versions
   */
  async getVersions(platform = null) {
    const params = {}
    if (platform) params.platform = platform
    return super.get('/versions', params)
  }

  /**
   * Get selector metadata.
   * 
   * @param {string} version - Selector version
   * @param {string} [platform] - Platform (threads, facebook)
   * @returns {Promise<Object>} API response with metadata
   */
  async getMetadata(version, platform = null) {
    const params = { version }
    if (platform) params.platform = platform
    return super.get('/metadata', params)
  }

  /**
   * Delete selector version.
   * 
   * @param {string} version - Selector version to delete
   * @param {string} [platform] - Platform (threads, facebook)
   * @returns {Promise<Object>} API response
   */
  async deleteVersion(version, platform = null) {
    const params = {}
    if (platform) params.platform = platform
    return this.delete(`/${version}`, { params })
  }
}

// Export singleton instance
export const selectorsService = new SelectorsService()
