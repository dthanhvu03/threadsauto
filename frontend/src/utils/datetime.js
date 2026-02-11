/**
 * Datetime formatting utilities for Vietnam timezone (UTC+7).
 * 
 * STRATEGY:
 * - Backend sends ISO UTC strings (e.g. "2026-02-10T03:15:00+00:00")
 * - Frontend converts UTC → VN time (UTC+7) for display
 * - Frontend converts VN form input → UTC for API calls
 */

const VN_OFFSET_MS = 7 * 60 * 60 * 1000 // +7 hours in milliseconds

/**
 * Parse an ISO string or Date into a proper Date object.
 * Handles 'Z' suffix, timezone offsets, and VN-formatted strings.
 * 
 * @param {Date|string|null} input 
 * @returns {Date|null}
 */
function parseDate(input) {
  if (!input) return null
  if (input instanceof Date) return isNaN(input.getTime()) ? null : input
  
  // If already VN-formatted (dd/MM/yyyy HH:mm:ss), parse it
  const vnMatch = input.match(/^(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2}):(\d{2})$/)
  if (vnMatch) {
    const [, day, month, year, hours, minutes, seconds] = vnMatch
    // This is already a VN display time, create Date from it
    // We treat it as UTC for internal use since it's display-only
    return new Date(Date.UTC(
      parseInt(year), parseInt(month) - 1, parseInt(day),
      parseInt(hours), parseInt(minutes), parseInt(seconds)
    ))
  }
  
  const d = new Date(input)
  return isNaN(d.getTime()) ? null : d
}

/**
 * Convert a UTC Date to Vietnam time components.
 * 
 * @param {Date} date - UTC date
 * @returns {{ year: number, month: number, day: number, hours: number, minutes: number, seconds: number }}
 */
function utcToVnComponents(date) {
  // Add 7 hours to get VN time, use UTC methods to avoid local offset interference
  const vnMs = date.getTime() + VN_OFFSET_MS
  const vn = new Date(vnMs)
  return {
    year: vn.getUTCFullYear(),
    month: vn.getUTCMonth() + 1,
    day: vn.getUTCDate(),
    hours: vn.getUTCHours(),
    minutes: vn.getUTCMinutes(),
    seconds: vn.getUTCSeconds()
  }
}

/**
 * Format datetime to VN: dd/MM/yyyy HH:mm:ss
 * 
 * Input: ISO UTC string from backend (e.g. "2026-02-10T03:15:00+00:00")
 * Output: "10/02/2026 10:15:00" (Vietnam time)
 * 
 * @param {Date|string|null} date
 * @returns {string}
 */
export function formatDateTimeVN(date) {
  // If already VN-formatted, return as-is
  if (typeof date === 'string' && /^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}$/.test(date)) {
    return date
  }
  
  const d = parseDate(date)
  if (!d) return ''
  
  const c = utcToVnComponents(d)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(c.day)}/${pad(c.month)}/${c.year} ${pad(c.hours)}:${pad(c.minutes)}:${pad(c.seconds)}`
}

/**
 * Format date to VN: dd/MM/yyyy
 * 
 * @param {Date|string|null} date
 * @returns {string}
 */
export function formatDateVN(date) {
  const d = parseDate(date)
  if (!d) return ''
  
  const c = utcToVnComponents(d)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(c.day)}/${pad(c.month)}/${c.year}`
}

/**
 * Format time to VN: HH:mm:ss
 * 
 * @param {Date|string|null} date
 * @returns {string}
 */
export function formatTimeVN(date) {
  const d = parseDate(date)
  if (!d) return ''
  
  const c = utcToVnComponents(d)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(c.hours)}:${pad(c.minutes)}:${pad(c.seconds)}`
}

/**
 * Convert datetime-local input (VN time) to UTC ISO string for API.
 * 
 * Input: "2026-02-10T10:15" (user typed VN time)
 * Output: "2026-02-10T03:15:00.000Z" (UTC for backend)
 * 
 * @param {string|null} datetimeLocal - "YYYY-MM-DDTHH:mm"
 * @returns {string|null} ISO UTC string
 */
export function datetimeLocalToUTC(datetimeLocal) {
  if (!datetimeLocal) return null
  
  try {
    const [datePart, timePart] = datetimeLocal.split('T')
    if (!datePart || !timePart) return null
    
    const [year, month, day] = datePart.split('-').map(Number)
    const [hours, minutes] = timePart.split(':').map(Number)
    
    // Create as UTC, then subtract 7h (because input is VN time)
    const vnAsUtc = new Date(Date.UTC(year, month - 1, day, hours, minutes, 0))
    const utcDate = new Date(vnAsUtc.getTime() - VN_OFFSET_MS)
    
    return utcDate.toISOString()
  } catch (error) {
    console.error('Error converting datetime-local to UTC:', error)
    return null
  }
}

/**
 * Convert UTC ISO string to datetime-local string (VN time) for form inputs.
 * 
 * Input: "2026-02-10T03:15:00.000Z" (UTC from backend)
 * Output: "2026-02-10T10:15" (VN time for <input type="datetime-local">)
 * 
 * @param {string|Date|null} isoString
 * @returns {string} "YYYY-MM-DDTHH:mm"
 */
export function utcToDatetimeLocal(isoString) {
  if (!isoString) return ''
  
  try {
    const d = parseDate(isoString)
    if (!d) return ''
    
    const c = utcToVnComponents(d)
    const pad = (n) => String(n).padStart(2, '0')
    return `${c.year}-${pad(c.month)}-${pad(c.day)}T${pad(c.hours)}:${pad(c.minutes)}`
  } catch (error) {
    console.error('Error converting UTC to datetime-local:', error)
    return ''
  }
}

/**
 * Convert Date to VN timezone Date object.
 * @deprecated Use formatDateTimeVN() or utcToVnComponents() instead.
 */
export function toVietnamTimezone(date) {
  const d = parseDate(date)
  if (!d) return null
  return new Date(d.getTime() + VN_OFFSET_MS)
}

/**
 * Convert VN timezone Date to UTC Date.
 * @deprecated Use datetimeLocalToUTC() instead.
 */
export function fromVietnamTimezone(date) {
  const d = parseDate(date)
  if (!d) return null
  return new Date(d.getTime() - VN_OFFSET_MS)
}
