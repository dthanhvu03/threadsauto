/**
 * Utility functions để sanitize dữ liệu nhạy cảm trước khi log hoặc gửi.
 */

// Default list of sensitive keys
const DEFAULT_SENSITIVE_KEYS = [
  'password', 'passwd', 'pwd',
  'token', 'access_token', 'refresh_token', 'auth_token',
  'secret', 'api_key', 'api_secret', 'private_key',
  'auth', 'authorization', 'credential', 'credentials',
  'content', 'text', 'message', 'body', 'data',
  'link_aff', 'affiliate_link', 'aff_link',
  'profile_path', 'user_data_dir', 'file_path', 'path',
  'traceback', 'stack_trace', 'error_traceback'
]

/**
 * Sanitize error message, loại bỏ file paths và internal structure.
 * 
 * @param {string|Error} error - Error string hoặc Error object
 * @returns {string} Sanitized error message
 */
export function sanitizeError(error) {
  let errorStr = ''
  let errorType = null
  
  if (error instanceof Error) {
    errorStr = error.message || String(error)
    errorType = error.constructor.name
  } else {
    errorStr = String(error)
  }
  
  // Loại bỏ file paths (absolute paths)
  // Pattern: /path/to/file hoặc C:\path\to\file
  errorStr = errorStr.replace(/[A-Za-z]:\\[^\s]+|\/[^\s]+\.(py|js|ts|json|yaml|yml)/g, '[FILE_PATH]')
  
  // Loại bỏ line numbers trong file paths
  errorStr = errorStr.replace(/line \d+/g, '[LINE]')
  
  // Loại bỏ internal structure details
  errorStr = errorStr.replace(/<[^>]+>/g, '[OBJECT]')
  
  // Nếu có error type, thêm vào đầu
  if (errorType) {
    return `${errorType}: ${errorStr}`
  }
  
  return errorStr
}

/**
 * Mask URL, giữ domain nhưng ẩn query params và path nếu nhạy cảm.
 * 
 * @param {string} url - URL string
 * @returns {string} Masked URL
 */
function maskUrl(url) {
  try {
    const parsed = new URL(url)
    // Giữ scheme và host (domain)
    // Mask path và query
    const maskedPath = parsed.pathname ? '/[REDACTED]' : ''
    const maskedQuery = parsed.search ? '?[REDACTED]' : ''
    
    return `${parsed.protocol}//${parsed.host}${maskedPath}${maskedQuery}`
  } catch (e) {
    // Nếu parse fail, return masked version
    return '[REDACTED_URL]'
  }
}

/**
 * Hash string content.
 * 
 * @param {string} content - Content to hash
 * @returns {string} Hash prefix
 */
async function hashContent(content) {
  if (typeof content !== 'string' || content.length === 0) {
    return '[REDACTED]'
  }
  
  try {
    // Use Web Crypto API if available
    if (typeof crypto !== 'undefined' && crypto.subtle) {
      const encoder = new TextEncoder()
      const data = encoder.encode(content)
      const hashBuffer = await crypto.subtle.digest('SHA-256', data)
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
      return `[HASH:${hashHex.substring(0, 16)}]`
    }
  } catch (e) {
    // Fallback if crypto not available
  }
  
  // Simple hash fallback
  let hash = 0
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // Convert to 32bit integer
  }
  return `[HASH:${Math.abs(hash).toString(16).substring(0, 16)}]`
}

/**
 * Sanitize một giá trị dựa trên key.
 * 
 * @param {string} key - Key name
 * @param {any} value - Value to sanitize
 * @returns {Promise<any>} Sanitized value
 */
async function sanitizeValue(key, value) {
  const keyLower = key.toLowerCase()
  
  // Password, token, secret fields
  if (['password', 'token', 'secret', 'api_key', 'auth', 'credential'].some(s => keyLower.includes(s))) {
    return '[REDACTED]'
  }
  
  // Content fields - hash thay vì redact hoàn toàn
  if (['content', 'text', 'message', 'body'].some(c => keyLower.includes(c))) {
    if (typeof value === 'string' && value.length > 0) {
      return await hashContent(value)
    }
    return '[REDACTED]'
  }
  
  // URL fields
  if (['link_aff', 'affiliate_link', 'aff_link', 'url'].some(u => keyLower.includes(u))) {
    if (typeof value === 'string') {
      return maskUrl(value)
    }
    return '[REDACTED]'
  }
  
  // Path fields
  if (['profile_path', 'user_data_dir', 'file_path', 'path'].some(p => keyLower.includes(p))) {
    if (typeof value === 'string') {
      // Mask path, chỉ giữ tên file cuối cùng nếu có
      const parts = value.replace(/\\/g, '/').split('/')
      if (parts.length > 0 && parts[parts.length - 1]) {
        return `[PATH:.../${parts[parts.length - 1]}]`
      }
      return '[REDACTED_PATH]'
    }
    return '[REDACTED]'
  }
  
  // Error fields
  if (keyLower === 'error' || keyLower === 'error_message') {
    return sanitizeError(value)
  }
  
  // Stack trace fields
  if (['traceback', 'stack_trace', 'error_traceback'].includes(keyLower)) {
    if (typeof value === 'string') {
      // Chỉ giữ error type và message, loại bỏ stack trace
      const lines = value.split('\n')
      if (lines.length > 0) {
        return sanitizeError(lines[0])
      }
      return '[REDACTED]'
    }
    return '[REDACTED]'
  }
  
  // Return original value nếu không phải sensitive
  return value
}

/**
 * Sanitize object data, loại bỏ hoặc mask các fields nhạy cảm.
 * 
 * @param {Object} data - Data object to sanitize
 * @param {string[]} sensitiveKeys - Optional list of additional sensitive keys
 * @returns {Promise<Object>} Sanitized object
 */
export async function sanitizeData(data, sensitiveKeys = []) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return data
  }
  
  const sensitiveKeysList = [...sensitiveKeys, ...DEFAULT_SENSITIVE_KEYS]
  const sanitized = {}
  
  for (const [key, value] of Object.entries(data)) {
    // Check if key is sensitive
    const keyLower = key.toLowerCase()
    const isSensitive = sensitiveKeysList.some(
      sensitiveKey => keyLower.includes(sensitiveKey.toLowerCase())
    )
    
    if (isSensitive) {
      sanitized[key] = await sanitizeValue(key, value)
    } else if (value && typeof value === 'object' && !Array.isArray(value)) {
      // Recursively sanitize nested objects
      sanitized[key] = await sanitizeData(value, sensitiveKeys)
    } else if (Array.isArray(value)) {
      // Sanitize array items
      sanitized[key] = await Promise.all(
        value.map(item => 
          typeof item === 'object' && item !== null 
            ? sanitizeData(item, sensitiveKeys) 
            : item
        )
      )
    } else {
      // Keep non-sensitive values as-is
      sanitized[key] = value
    }
  }
  
  return sanitized
}

/**
 * Sanitize log data cho console.log (synchronous version).
 * 
 * @param {Object} data - Data to sanitize
 * @returns {Object} Sanitized data (synchronous, không hash content)
 */
export function sanitizeLogData(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return data
  }
  
  const sensitiveKeysList = DEFAULT_SENSITIVE_KEYS
  const sanitized = {}
  
  for (const [key, value] of Object.entries(data)) {
    const keyLower = key.toLowerCase()
    const isSensitive = sensitiveKeysList.some(
      sensitiveKey => keyLower.includes(sensitiveKey.toLowerCase())
    )
    
    if (isSensitive) {
      // For console logs, just redact sensitive fields
      if (['content', 'text', 'message', 'body'].some(c => keyLower.includes(c))) {
        sanitized[key] = '[REDACTED_CONTENT]'
      } else if (keyLower === 'error' || keyLower === 'error_message') {
        sanitized[key] = sanitizeError(value)
      } else {
        sanitized[key] = '[REDACTED]'
      }
    } else if (value && typeof value === 'object' && !Array.isArray(value)) {
      sanitized[key] = sanitizeLogData(value)
    } else if (Array.isArray(value)) {
      sanitized[key] = value.map(item => 
        typeof item === 'object' && item !== null 
          ? sanitizeLogData(item) 
          : item
      )
    } else {
      sanitized[key] = value
    }
  }
  
  return sanitized
}
