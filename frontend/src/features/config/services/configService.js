/**
 * Config API service.
 * 
 * Handles all API calls for config feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Config service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class ConfigService extends BaseService {
  constructor() {
    super('/config')
  }

  /**
   * Get configuration.
   * 
   * @returns {Promise<Object>} API response with config data
   */
  async get() {
    return super.get('')
  }

  /**
   * Update configuration.
   * 
   * @param {Object} configData - Configuration data
   * @returns {Promise<Object>} API response with updated config
   */
  async update(configData) {
    return this.put('', configData)
  }
}

// Export singleton instance
export const configService = new ConfigService()
