/**
 * Excel composable.
 * 
 * Provides business logic for Excel upload operations.
 */

import { ref } from 'vue'
import { excelService } from '../services/excelService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for Excel feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useExcel() {
  const loading = ref(false)
  const error = ref(null)
  const uploadResult = ref(null)

  /**
   * Upload Excel file.
   * 
   * @param {File} file - Excel file to upload
   * @param {string} [accountId] - Optional account ID
   * @returns {Promise<Object|null>} Upload result or null on error
   */
  const uploadFile = async (file, accountId = null) => {
    loading.value = true
    error.value = null
    uploadResult.value = null

    try {
      if (!file) {
        throw new Error('Please select a file')
      }

      const result = await excelService.upload(file, accountId)
      uploadResult.value = result
      return result
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Download template file.
   * 
   * @returns {Promise<Blob|null>} Template blob or null on error
   */
  const downloadTemplate = async () => {
    loading.value = true
    error.value = null

    try {
      const blob = await excelService.downloadTemplate()
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'job_template.json'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      return blob
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error.
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * Clear upload result.
   */
  const clearResult = () => {
    uploadResult.value = null
  }

  return {
    loading,
    error,
    uploadResult,
    uploadFile,
    downloadTemplate,
    clearError,
    clearResult
  }
}
