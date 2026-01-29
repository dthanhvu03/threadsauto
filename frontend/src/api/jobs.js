/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/jobs/services/jobsService
 * 
 * This file will be removed in a future version.
 * Please migrate to using jobsService or useJobs composable.
 */

import apiClient from './client'

export const jobsApi = {
  getAll: (accountId = null, reload = false) => {
    const params = {}
    if (accountId) params.account_id = accountId
    if (reload) params.reload = reload
    return apiClient.get('/jobs', { params })
  },

  getById: (jobId) => {
    return apiClient.get(`/jobs/${jobId}`)
  },

  create: (jobData) => {
    return apiClient.post('/jobs', jobData)
  },

  update: (jobId, jobData) => {
    return apiClient.put(`/jobs/${jobId}`, jobData)
  },

  delete: (jobId) => {
    return apiClient.delete(`/jobs/${jobId}`)
  }
}
