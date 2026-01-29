/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/excel/services/excelService
 * 
 * This file will be removed in a future version.
 * Please migrate to using excelService or useExcel composable.
 */

import apiClient from './client'

export const excelApi = {
  upload: (file, accountId = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (accountId) {
      formData.append('account_id', accountId)
    }
    return apiClient.post('/excel/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  downloadTemplate: () => {
    return apiClient.get('/excel/template', {
      responseType: 'blob',
    })
  }
}
