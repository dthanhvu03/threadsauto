/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/dashboard/services/dashboardService
 * 
 * This file will be removed in a future version.
 * Please migrate to using dashboardService or useDashboard composable.
 */

import apiClient from './client'

export const dashboardApi = {
  getStats: (accountId = null) => {
    const params = {}
    if (accountId) params.account_id = accountId
    return apiClient.get('/dashboard/stats', { params })
  },

  getMetrics: (accountId = null) => {
    const params = {}
    if (accountId) params.account_id = accountId
    return apiClient.get('/dashboard/metrics', { params })
  },

  getActivity: (accountId = null, limit = 10) => {
    const params = { limit }
    if (accountId) params.account_id = accountId
    return apiClient.get('/dashboard/activity', { params })
  }
}
