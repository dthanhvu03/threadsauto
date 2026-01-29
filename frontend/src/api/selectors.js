/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/selectors/services/selectorsService
 * 
 * This file will be removed in a future version.
 * Please migrate to using selectorsService or useSelectors composable.
 */

import apiClient from './client'

export const selectorsApi = {
  get: (version = null, platform = 'threads') => {
    const params = { platform }
    if (version) params.version = version
    return apiClient.get('/selectors', { params })
  },

  update: (selectorsData) => {
    return apiClient.put('/selectors', selectorsData)
  },

  getVersions: (platform = 'threads') => {
    return apiClient.get('/selectors/versions', { params: { platform } })
  },

  getMetadata: (version = 'v1', platform = 'threads') => {
    return apiClient.get('/selectors/metadata', { params: { version, platform } })
  },

  deleteVersion: (version, platform = 'threads') => {
    return apiClient.delete(`/selectors/${version}`, { params: { platform } })
  }
}
