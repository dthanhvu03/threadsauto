/**
 * Dashboard API service.
 * 
 * Handles all API calls for dashboard feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Dashboard service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class DashboardService extends BaseService {
  constructor() {
    super('/dashboard')
  }

  /**
   * Get dashboard statistics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<Object>} API response with dashboard stats
   */
  async getStats(accountId = null) {
    const params = {}
    if (accountId) params.account_id = accountId
    return this.get('/stats', params)
  }

  /**
   * Get dashboard metrics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<Object>} API response with dashboard metrics
   */
  async getMetrics(accountId = null) {
    const params = {}
    if (accountId) params.account_id = accountId
    return this.get('/metrics', params)
  }

  /**
   * Get recent activity.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @param {number} [limit=10] - Number of activities to return
   * @returns {Promise<Array>} API response with recent activity
   */
  async getActivity(accountId = null, limit = 10) {
    const params = { limit }
    if (accountId) params.account_id = accountId
    return this.get('/activity', params)
  }
}

// Export singleton instance
export const dashboardService = new DashboardService()
