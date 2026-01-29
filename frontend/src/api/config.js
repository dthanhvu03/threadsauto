/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/config/services/configService
 * 
 * This file will be removed in a future version.
 * Please migrate to using configService or useConfig composable.
 */

import apiClient from './client'

export const configApi = {
  get: () => {
    return apiClient.get('/config')
  },

  update: (configData) => {
    return apiClient.put('/config', configData)
  }
}
