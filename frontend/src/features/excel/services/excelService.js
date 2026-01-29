/**
 * Excel service.
 * 
 * API service for Excel operations.
 * Extends BaseService to provide common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Excel service class.
 * 
 * @class
 */
class ExcelService extends BaseService {
  /**
   * Create Excel service.
   */
  constructor() {
    super('/excel')
  }

  /**
   * Upload Excel file.
   * 
   * @param {File} file - Excel file to upload
   * @param {string} [accountId] - Optional account ID
   * @returns {Promise<Object>} Upload result
   */
  async upload(file, accountId = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (accountId) {
      formData.append('account_id', accountId)
    }
    
    // When sending FormData, do NOT set Content-Type header - let browser set it with boundary
    return this.post('/upload', formData)
  }

  /**
   * Download template file.
   * 
   * @returns {Promise<Blob>} Template file blob
   */
  async downloadTemplate() {
    return this.client.get('/excel/template', {
      responseType: 'blob',
    })
  }
}

export const excelService = new ExcelService()
