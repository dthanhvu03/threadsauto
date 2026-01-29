/**
 * API client - Re-export from core for backward compatibility.
 * 
 * All API files should use this client which handles standard response format.
 * The client automatically extracts data from success responses and throws ApiError for errors.
 */

import apiClient from '@/core/api/client'

export default apiClient
