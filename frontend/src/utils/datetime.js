/**
 * Datetime formatting utilities for Vietnam timezone (UTC+7).
 * 
 * All datetime values are converted from UTC to Vietnam timezone (Asia/Ho_Chi_Minh)
 * and formatted according to Vietnamese date format standards.
 */

/**
 * Convert a date to Vietnam timezone (UTC+7).
 * 
 * @param {Date|string|null|undefined} date - Date to convert
 * @returns {Date|null} Date in Vietnam timezone or null if invalid
 */
export function toVietnamTimezone(date) {
  if (!date) return null
  
  try {
    const d = date instanceof Date ? date : new Date(date)
    if (isNaN(d.getTime())) return null
    
    // Get UTC time
    const utcTime = d.getTime()
    // Vietnam is UTC+7, so add 7 hours (7 * 60 * 60 * 1000 ms)
    const vnOffset = 7 * 60 * 60 * 1000
    const vnTime = new Date(utcTime + vnOffset)
    
    return vnTime
  } catch (error) {
    console.error('Error converting to Vietnam timezone:', error)
    return null
  }
}

/**
 * Format datetime to Vietnam format: dd/MM/yyyy HH:mm:ss
 * 
 * @param {Date|string|null|undefined} date - Date to format
 * @returns {string} Formatted datetime string or empty string if invalid
 * 
 * @example
 * formatDateTimeVN('2026-01-26T07:30:45Z') // Returns "26/01/2026 14:30:45"
 */
export function formatDateTimeVN(date) {
  // If input is already a VN-formatted string (dd/MM/yyyy HH:mm:ss), return it directly
  if (typeof date === 'string' && /^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}$/.test(date)) {
    return date
  }
  
  const vnDate = toVietnamTimezone(date)
  if (!vnDate) return ''
  
  try {
    // Use local date methods since vnDate is already in Vietnam timezone
    const day = String(vnDate.getDate()).padStart(2, '0')
    const month = String(vnDate.getMonth() + 1).padStart(2, '0')
    const year = vnDate.getFullYear()
    const hours = String(vnDate.getHours()).padStart(2, '0')
    const minutes = String(vnDate.getMinutes()).padStart(2, '0')
    const seconds = String(vnDate.getSeconds()).padStart(2, '0')
    
    return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`
  } catch (error) {
    console.error('Error formatting datetime:', error)
    return ''
  }
}

/**
 * Format date to Vietnam format: dd/MM/yyyy
 * 
 * @param {Date|string|null|undefined} date - Date to format
 * @returns {string} Formatted date string or empty string if invalid
 * 
 * @example
 * formatDateVN('2026-01-26T07:30:45Z') // Returns "26/01/2026"
 */
export function formatDateVN(date) {
  const vnDate = toVietnamTimezone(date)
  if (!vnDate) return ''
  
  try {
    // Use local date methods since vnDate is already in Vietnam timezone
    const day = String(vnDate.getDate()).padStart(2, '0')
    const month = String(vnDate.getMonth() + 1).padStart(2, '0')
    const year = vnDate.getFullYear()
    
    return `${day}/${month}/${year}`
  } catch (error) {
    console.error('Error formatting date:', error)
    return ''
  }
}

/**
 * Format time to Vietnam format: HH:mm:ss
 * 
 * @param {Date|string|null|undefined} date - Date to format
 * @returns {string} Formatted time string or empty string if invalid
 * 
 * @example
 * formatTimeVN('2026-01-26T07:30:45Z') // Returns "14:30:45"
 */
export function formatTimeVN(date) {
  const vnDate = toVietnamTimezone(date)
  if (!vnDate) return ''
  
  try {
    // Use local time methods since vnDate is already in Vietnam timezone
    const hours = String(vnDate.getHours()).padStart(2, '0')
    const minutes = String(vnDate.getMinutes()).padStart(2, '0')
    const seconds = String(vnDate.getSeconds()).padStart(2, '0')
    
    return `${hours}:${minutes}:${seconds}`
  } catch (error) {
    console.error('Error formatting time:', error)
    return ''
  }
}

/**
 * Convert datetime from Vietnam timezone (UTC+7) to UTC for API submission.
 * 
 * @param {Date|string|null|undefined} date - Date in Vietnam timezone
 * @returns {Date|null} Date in UTC or null if invalid
 */
export function fromVietnamTimezone(date) {
  if (!date) return null
  
  try {
    const d = date instanceof Date ? date : new Date(date)
    if (isNaN(d.getTime())) return null
    
    // If date is already a Date object from datetime-local input, it's in local timezone
    // We need to treat it as Vietnam timezone and convert to UTC
    // Get the time value
    const timeValue = d.getTime()
    // Get local timezone offset in minutes
    const localOffset = d.getTimezoneOffset() * 60 * 1000
    // Get Vietnam timezone offset (UTC+7 = -420 minutes)
    const vnOffset = -7 * 60 * 60 * 1000
    // Calculate UTC time: local time - local offset + VN offset
    const utcTime = timeValue - localOffset + vnOffset
    
    return new Date(utcTime)
  } catch (error) {
    console.error('Error converting from Vietnam timezone:', error)
    return null
  }
}

/**
 * Convert datetime-local string (YYYY-MM-DDTHH:mm) from Vietnam timezone to UTC ISO string.
 * Used when submitting forms.
 * 
 * @param {string|null|undefined} datetimeLocal - Datetime-local string (e.g., "2026-01-26T14:30")
 * @returns {string|null} ISO string in UTC or null if invalid
 */
export function datetimeLocalToUTC(datetimeLocal) {
  if (!datetimeLocal) return null
  
  try {
    // Parse datetime-local as if it's in Vietnam timezone
    // datetime-local format: YYYY-MM-DDTHH:mm
    const [datePart, timePart] = datetimeLocal.split('T')
    if (!datePart || !timePart) return null
    
    const [year, month, day] = datePart.split('-').map(Number)
    const [hours, minutes] = timePart.split(':').map(Number)
    
    // Create date assuming it's in Vietnam timezone (UTC+7)
    // We'll create a UTC date and subtract 7 hours
    const vnDate = new Date(Date.UTC(year, month - 1, day, hours, minutes, 0))
    // Subtract 7 hours to get UTC
    const utcDate = new Date(vnDate.getTime() - 7 * 60 * 60 * 1000)
    
    return utcDate.toISOString()
  } catch (error) {
    console.error('Error converting datetime-local to UTC:', error)
    return null
  }
}

/**
 * Convert UTC ISO string to datetime-local string (YYYY-MM-DDTHH:mm) in Vietnam timezone.
 * Used when displaying datetime in input fields.
 * 
 * @param {string|Date|null|undefined} isoString - ISO string in UTC or Date object
 * @returns {string} Datetime-local string or empty string if invalid
 */
export function utcToDatetimeLocal(isoString) {
  if (!isoString) return ''
  
  try {
    const date = isoString instanceof Date ? isoString : new Date(isoString)
    if (isNaN(date.getTime())) return ''
    
    // Convert UTC to Vietnam timezone (add 7 hours)
    const vnDate = new Date(date.getTime() + 7 * 60 * 60 * 1000)
    
    // Use local date methods since vnDate represents Vietnam timezone
    const year = vnDate.getFullYear()
    const month = String(vnDate.getMonth() + 1).padStart(2, '0')
    const day = String(vnDate.getDate()).padStart(2, '0')
    const hours = String(vnDate.getHours()).padStart(2, '0')
    const minutes = String(vnDate.getMinutes()).padStart(2, '0')
    
    return `${year}-${month}-${day}T${hours}:${minutes}`
  } catch (error) {
    console.error('Error converting UTC to datetime-local:', error)
    return ''
  }
}
