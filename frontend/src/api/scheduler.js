/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/scheduler/services/schedulerService
 * 
 * This file will be removed in a future version.
 * Please migrate to using schedulerService or useScheduler composable.
 */

import apiClient from './client'

export const schedulerApi = {
  start: (accountId = null) => {
    const data = {}
    if (accountId) data.account_id = accountId
    return apiClient.post('/scheduler/start', data)
  },

  stop: () => {
    return apiClient.post('/scheduler/stop')
  },

  getStatus: () => {
    return apiClient.get('/scheduler/status')
  },

  getActiveJobs: () => {
    return apiClient.get('/scheduler/jobs')
  }
}
