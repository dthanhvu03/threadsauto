/**
 * Scheduler API service.
 * 
 * Handles all API calls for scheduler feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Scheduler service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class SchedulerService extends BaseService {
  constructor() {
    super('/scheduler')
  }

  /**
   * Start scheduler.
   * 
   * @param {string} [accountId] - Optional account ID
   * @returns {Promise<Object>} API response
   */
  async start(accountId = null) {
    const data = {}
    if (accountId) data.account_id = accountId
    return this.post('/start', data)
  }

  /**
   * Stop scheduler.
   * 
   * @returns {Promise<Object>} API response
   */
  async stop() {
    return this.post('/stop')
  }

  /**
   * Get scheduler status.
   * 
   * @returns {Promise<Object>} API response with scheduler status
   */
  async getStatus() {
    return this.get('/status')
  }

  /**
   * Get active jobs.
   * 
   * @returns {Promise<Array>} API response with active jobs
   */
  async getActiveJobs() {
    return this.get('/jobs')
  }
}

// Export singleton instance
export const schedulerService = new SchedulerService()
