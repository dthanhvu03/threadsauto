/**
 * Standardized API client with interceptors.
 * 
 * Provides consistent error handling and request/response transformation.
 */

import axios from 'axios'
import { ApiError, ErrorCodes, isErrorResponse } from './types'

/**
 * Create API client instance.
 * 
 * @param {string} baseURL - Base URL for API
 * @returns {import('axios').AxiosInstance}
 */
export function createApiClient(baseURL = '/api') {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add auth token if needed
      // const token = getAuthToken()
      // if (token) {
      //   config.headers.Authorization = `Bearer ${token}`
      // }
      
      // When sending FormData, remove Content-Type header to let browser set it with boundary
      // Axios will automatically set multipart/form-data with proper boundary for FormData
      if (config.data instanceof FormData) {
        delete config.headers['Content-Type']
      }
      
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      // Backend returns standard response format: {success: true, data: {...}, message: "...", meta: {...}}
      const responseData = response.data
      
      // Check if response is error response
      if (isErrorResponse(responseData)) {
        const error = responseData.error
        throw new ApiError(
          error.code || ErrorCodes.INTERNAL_ERROR,
          error.message || 'An error occurred',
          error.details || {},
          response.status
        )
      }
      
      // Extract data from success response
      // Standard format: {success: true, data: {...}, message: "...", meta: {...}, pagination: {...}}
      if (responseData && responseData.success === true) {
        const data = responseData.data
        
        // If data is an array, preserve metadata (pagination or meta)
        if (Array.isArray(data)) {
          if (responseData.pagination || responseData.meta) {
            return {
              data: data,
              _pagination: responseData.pagination || null,
              _meta: responseData.meta || null
            }
          }
          // For arrays without metadata, return as-is
          return data
        }
        
        // For non-array data, attach properties directly
        if (data && typeof data === 'object' && !Array.isArray(data)) {
          if (responseData.meta) {
            data._meta = responseData.meta
          }
          if (responseData.pagination) {
            data._pagination = responseData.pagination
          }
          return data
        }
        
        // For primitive data, return as-is
        return data
      }
      
      // Fallback: return response data as-is if format is unexpected
      return responseData
    },
    (error) => {
      // Handle axios errors
      if (error.response) {
        // Server responded with error
        const errorData = error.response.data || {}
        
        // Check if it's a standard error response
        if (isErrorResponse(errorData)) {
          const apiError = errorData.error
          throw new ApiError(
            apiError.code || ErrorCodes.INTERNAL_ERROR,
            apiError.message || 'An error occurred',
            apiError.details || {},
            error.response.status
          )
        }
        
        // Fallback for non-standard error responses
        throw new ApiError(
          ErrorCodes.HTTP_ERROR,
          errorData.message || errorData.error || 'An error occurred',
          errorData,
          error.response.status
        )
      } else if (error.request) {
        // Request made but no response
        const errorMessage = error.code === 'ECONNREFUSED' 
          ? 'Cannot connect to backend API. Please ensure the backend server is running.'
          : error.message || 'Network error. Please check your connection.'
        throw new ApiError(
          ErrorCodes.INTERNAL_ERROR,
          errorMessage,
          {
            code: error.code,
            message: error.message,
            config: {
              url: error.config?.url,
              baseURL: error.config?.baseURL,
              method: error.config?.method
            }
          },
          0
        )
      } else {
        // Something else happened
        if (error instanceof ApiError) {
          throw error
        }
        throw new ApiError(
          ErrorCodes.INTERNAL_ERROR,
          error.message || 'An unexpected error occurred',
          {},
          0
        )
      }
    }
  )

  return client
}

// Default API client instance
const apiClient = createApiClient()

export default apiClient
