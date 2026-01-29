/**
 * API response types and type definitions.
 * 
 * Defines standard response formats and error structures
 * matching the backend API contract.
 */

/**
 * Standard API success response.
 * 
 * @typedef {Object} ApiSuccessResponse
 * @property {boolean} success - Always true for success responses
 * @property {*} data - Response data (can be any type)
 * @property {string} [message] - Optional success message
 * @property {Object} meta - Metadata
 * @property {string} meta.timestamp - ISO timestamp
 * @property {string} meta.request_id - Request ID for tracing
 * @property {Object} [pagination] - Pagination metadata (if applicable)
 * @property {number} pagination.page - Current page number
 * @property {number} pagination.limit - Items per page
 * @property {number} pagination.total - Total number of items
 * @property {number} pagination.total_pages - Total number of pages
 * @property {boolean} pagination.has_next - Whether there is a next page
 * @property {boolean} pagination.has_prev - Whether there is a previous page
 */

/**
 * Standard API error response.
 * 
 * @typedef {Object} ApiErrorResponse
 * @property {boolean} success - Always false for error responses
 * @property {Object} error - Error information
 * @property {string} error.code - Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
 * @property {string} error.message - Error message
 * @property {Object} [error.details] - Additional error details
 * @property {Object} meta - Metadata
 * @property {string} meta.timestamp - ISO timestamp
 * @property {string} meta.request_id - Request ID for tracing
 */

/**
 * Standard API response (success or error).
 * 
 * @typedef {ApiSuccessResponse|ApiErrorResponse} ApiResponse
 */

/**
 * Error codes from backend.
 * 
 * Maps to backend error codes defined in app/core/exceptions.py
 * 
 * @enum {string}
 */
export const ErrorCodes = {
  // Authentication & Authorization
  AUTH_REQUIRED: 'AUTH_REQUIRED',
  AUTH_INVALID: 'AUTH_INVALID',
  AUTH_EXPIRED: 'AUTH_EXPIRED',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  
  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
  INVALID_FORMAT: 'INVALID_FORMAT',
  
  // Resources
  NOT_FOUND: 'NOT_FOUND',
  ALREADY_EXISTS: 'ALREADY_EXISTS',
  CONFLICT: 'CONFLICT',
  
  // Server
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
  DATABASE_ERROR: 'DATABASE_ERROR',
  
  // HTTP
  BAD_REQUEST: 'BAD_REQUEST',
  HTTP_ERROR: 'HTTP_ERROR'
}

/**
 * API error class.
 * 
 * @class
 * @extends {Error}
 */
export class ApiError extends Error {
  /**
   * Create API error.
   * 
   * @param {string} code - Error code
   * @param {string} message - Error message
   * @param {Object} [details] - Error details
   * @param {number} [status] - HTTP status code
   */
  constructor(code, message, details = {}, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.message = message
    this.details = details
    this.status = status
  }

  /**
   * Check if error is a specific error code.
   * 
   * @param {string} code - Error code to check
   * @returns {boolean}
   */
  is(code) {
    return this.code === code
  }

  /**
   * Check if error is a validation error.
   * 
   * @returns {boolean}
   */
  isValidationError() {
    return this.is(ErrorCodes.VALIDATION_ERROR)
  }

  /**
   * Check if error is a not found error.
   * 
   * @returns {boolean}
   */
  isNotFound() {
    return this.is(ErrorCodes.NOT_FOUND)
  }

  /**
   * Check if error is an unauthorized error.
   * 
   * @returns {boolean}
   */
  isUnauthorized() {
    return this.is(ErrorCodes.UNAUTHORIZED)
  }
}

/**
 * Type guard to check if response is success.
 * 
 * @param {ApiResponse} response - API response
 * @returns {response is ApiSuccessResponse}
 */
export function isSuccessResponse(response) {
  return response && response.success === true
}

/**
 * Type guard to check if response is error.
 * 
 * @param {ApiResponse} response - API response
 * @returns {response is ApiErrorResponse}
 */
export function isErrorResponse(response) {
  return response && response.success === false
}
