/**
 * Error handling utilities.
 * 
 * Provides common error handling functions and helpers.
 */

import { ApiError, ErrorCodes } from '../api/types'

/**
 * Get user-friendly error message.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {string} User-friendly error message
 */
export function getErrorMessage(error) {
  if (error instanceof ApiError) {
    return error.message
  }
  
  if (error?.response?.data?.error?.message) {
    return error.response.data.error.message
  }
  
  if (error?.message) {
    return error.message
  }
  
  return 'An unexpected error occurred'
}

/**
 * Get error code from error.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {string} Error code
 */
export function getErrorCode(error) {
  if (error instanceof ApiError) {
    return error.code
  }
  
  if (error?.response?.data?.error?.code) {
    return error.response.data.error.code
  }
  
  return ErrorCodes.INTERNAL_ERROR
}

/**
 * Check if error is a specific type.
 * 
 * @param {Error|ApiError} error - Error object
 * @param {string} code - Error code to check
 * @returns {boolean}
 */
export function isErrorCode(error, code) {
  return getErrorCode(error) === code
}

/**
 * Check if error is a validation error.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {boolean}
 */
export function isValidationError(error) {
  return isErrorCode(error, ErrorCodes.VALIDATION_ERROR)
}

/**
 * Check if error is a not found error.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {boolean}
 */
export function isNotFoundError(error) {
  return isErrorCode(error, ErrorCodes.NOT_FOUND)
}

/**
 * Check if error is an unauthorized error.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {boolean}
 */
export function isUnauthorizedError(error) {
  return isErrorCode(error, ErrorCodes.UNAUTHORIZED)
}

/**
 * Format validation errors for display.
 * 
 * @param {Error|ApiError} error - Error object
 * @returns {Object} Formatted validation errors
 */
export function formatValidationErrors(error) {
  if (!isValidationError(error)) {
    return {}
  }
  
  if (error instanceof ApiError && error.details?.errors) {
    const formatted = {}
    error.details.errors.forEach((err) => {
      const field = err.loc?.join('.') || 'unknown'
      formatted[field] = err.msg || 'Invalid value'
    })
    return formatted
  }
  
  return {}
}
