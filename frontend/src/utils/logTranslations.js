/**
 * Translation utilities for automation log messages.
 * 
 * Translates technical step names to user-friendly Vietnamese messages.
 */

/**
 * Mapping từ step names sang messages tiếng Việt dễ hiểu.
 */
const STEP_NAME_TRANSLATIONS = {
  // Browser operations
  'BROWSER_START': 'Đang khởi động trình duyệt',
  'BROWSER_CLOSE': 'Đang đóng trình duyệt',
  'NAVIGATE': 'Đang điều hướng',
  'NAVIGATE_TO_THREADS': 'Đang điều hướng đến Threads',
  'NAVIGATE_TO_COMPOSE': 'Đang điều hướng đến trang tạo bài viết',
  
  // Login operations
  'CHECK_LOGIN_STATE': 'Đang kiểm tra trạng thái đăng nhập',
  'CHECK_FACEBOOK_LOGIN_STATE': 'Đang kiểm tra trạng thái đăng nhập Facebook',
  'CLICK_INSTAGRAM_LOGIN': 'Đang click nút đăng nhập Instagram',
  'WAIT_MANUAL_LOGIN': 'Đang chờ đăng nhập thủ công',
  
  // Compose operations
  'CLICK_COMPOSE_BUTTON': 'Đang click nút tạo bài viết',
  'FIND_COMPOSE_INPUT': 'Đang tìm ô nhập nội dung',
  'COMPOSE_INPUT_NOT_FOUND': 'Không tìm thấy ô nhập nội dung',
  'WAIT_FOR_COMPOSE_FORM': 'Đang chờ form tạo bài viết',
  'TYPE_CONTENT': 'Đang nhập nội dung',
  
  // Post operations
  'POST_THREAD': 'Đang đăng bài',
  'FIND_POST_BUTTON': 'Đang tìm nút đăng',
  'CLICK_POST_BUTTON': 'Đang click nút đăng',
  'CLICK_ADD_TO_THREAD_BUTTON': 'Đang click nút thêm vào thread',
  'CHECK_LINK_AFF': 'Đang kiểm tra link affiliate',
  'CHECK_SHADOW_FAIL': 'Đang kiểm tra shadow fail',
  'DETECT_UI_STATE': 'Đang phát hiện trạng thái UI',
  
  // Verification operations
  'EXTRACT_THREAD_ID_FROM_PROFILE': 'Đang lấy ID bài viết',
  'EXTRACT_THREAD_ID_FROM_DOM': 'Đang lấy ID bài viết từ DOM',
  'EXTRACT_THREAD_ID_FROM_URL': 'Đang lấy ID bài viết từ URL',
  'VERIFY_POST_SUCCESS': 'Đang xác minh đăng bài thành công',
  
  // Job operations
  'RUN_JOB': 'Đang chạy job',
  'ADD_JOB': 'Đang thêm job',
  'UPDATE_JOB_STATUS': 'Đang cập nhật trạng thái job',
  
  // Username extraction
  'EXTRACT_USERNAME': 'Đang lấy tên người dùng',
  'EXTRACT_USERNAME_NAVIGATE': 'Đang điều hướng để lấy tên người dùng',
  
  // Metrics operations
  'FETCH_METRICS': 'Đang lấy metrics',
  'FETCH_METRICS_BUILD_URL': 'Đang tạo URL để lấy metrics',
  'SCRAPE_METRICS': 'Đang scrape metrics',
  
  // Navigation operations
  'NAVIGATE_TO_COMPOSE': 'Đang điều hướng đến trang tạo bài viết',
  
  // Unknown/fallback
  'UNKNOWN': 'Không xác định'
}

/**
 * Mapping từ operation names sang messages tiếng Việt.
 */
const OPERATION_NAME_TRANSLATIONS = {
  'run_job': 'Bắt đầu chạy job',
  'post_thread': 'Bắt đầu đăng bài',
  'post_facebook': 'Bắt đầu đăng bài Facebook'
}

/**
 * Mapping từ result status sang messages tiếng Việt.
 */
const RESULT_TRANSLATIONS = {
  'SUCCESS': 'Thành công',
  'FAILED': 'Thất bại',
  'ERROR': 'Lỗi',
  'IN_PROGRESS': 'Đang thực hiện',
  'WARNING': 'Cảnh báo',
  'COMPLETED': 'Hoàn thành',
  'DETECTED': 'Đã phát hiện',
  'FOUND': 'Đã tìm thấy',
  'NOT_FOUND': 'Không tìm thấy'
}

/**
 * Translate step name sang message tiếng Việt dễ hiểu.
 * 
 * @param {string} stepName - Step name gốc (ví dụ: "CLICK_COMPOSE_BUTTON")
 * @returns {string} Message tiếng Việt (ví dụ: "Đang click nút tạo bài viết")
 */
export function translateStepName(stepName) {
  if (!stepName || typeof stepName !== 'string') {
    return 'Không xác định'
  }
  
  // Check trong step name translations
  if (STEP_NAME_TRANSLATIONS[stepName]) {
    return STEP_NAME_TRANSLATIONS[stepName]
  }
  
  // Check trong operation name translations
  if (OPERATION_NAME_TRANSLATIONS[stepName]) {
    return OPERATION_NAME_TRANSLATIONS[stepName]
  }
  
  // Fallback: format step name để dễ đọc hơn
  // Convert SNAKE_CASE sang readable text
  const readable = stepName
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase())
  
  return readable
}

/**
 * Translate result status sang message tiếng Việt.
 * 
 * @param {string} result - Result status (ví dụ: "SUCCESS", "FAILED")
 * @returns {string} Message tiếng Việt (ví dụ: "Thành công", "Thất bại")
 */
export function translateResult(result) {
  if (!result || typeof result !== 'string') {
    return ''
  }
  
  const upperResult = result.toUpperCase()
  if (RESULT_TRANSLATIONS[upperResult]) {
    return RESULT_TRANSLATIONS[upperResult]
  }
  
  // Fallback: return original nếu không tìm thấy
  return result
}

/**
 * Get all available step name translations (for debugging).
 * 
 * @returns {Object} Mapping object
 */
export function getStepNameTranslations() {
  return { ...STEP_NAME_TRANSLATIONS }
}

/**
 * Get all available result translations (for debugging).
 * 
 * @returns {Object} Mapping object
 */
export function getResultTranslations() {
  return { ...RESULT_TRANSLATIONS }
}
