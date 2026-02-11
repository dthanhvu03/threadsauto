<template>
  <Teleport to="body">
    <Transition name="media-gallery">
      <div
        v-if="modelValue"
        ref="viewerRef"
        class="fixed inset-0 z-50 overflow-hidden"
        @click.self="handleClose"
        @keydown="handleKeydown"
        @mouseenter="isHovered = true"
        @mouseleave="isHovered = false"
        tabindex="-1"
      >
        <!-- Dark overlay -->
        <div class="fixed inset-0 bg-black bg-opacity-90 transition-opacity" />

        <!-- Gallery container with flex layout -->
        <div class="relative h-full w-full flex flex-col">
          <!-- Top bar: Close button and counter -->
          <div class="absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-4 pointer-events-none">
            <!-- Close button -->
            <button
              @click="handleClose"
              class="pointer-events-auto p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white"
              aria-label="Close gallery"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>

            <!-- Media counter -->
            <div
              v-if="mediaUrls.length > 1"
              class="px-3 py-1 rounded-full bg-black bg-opacity-50 text-white text-sm font-medium pointer-events-none"
            >
              {{ currentIndex + 1 }} / {{ mediaUrls.length }}
            </div>

            <!-- Spacer for symmetry -->
            <div class="w-10" />
          </div>

          <!-- Main media area (flex-1, centered) -->
          <div
            class="flex-1 min-h-0 flex items-center justify-center p-4 relative"
            :class="{ 'pb-32': mediaUrls.length > 1 }"
          >
            <!-- Navigation arrows (hover visible) -->
            <button
              v-if="mediaUrls.length > 1 && currentIndex > 0"
              @click="handlePrevious"
              :class="[
                'absolute left-4 z-10 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white',
                isHovered ? 'opacity-100' : 'opacity-0'
              ]"
              aria-label="Previous media"
            >
              <ChevronLeftIcon class="w-6 h-6" />
            </button>

            <button
              v-if="mediaUrls.length > 1 && currentIndex < mediaUrls.length - 1"
              @click="handleNext"
              :class="[
                'absolute right-4 z-10 p-3 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white',
                isHovered ? 'opacity-100' : 'opacity-0'
              ]"
              aria-label="Next media"
            >
              <ChevronRightIcon class="w-6 h-6" />
            </button>

            <!-- Media container -->
            <div class="relative max-w-full max-h-full flex items-center justify-center w-full">
              <!-- Loading state -->
              <div v-if="loading" class="flex flex-col items-center gap-4 text-white">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                <p class="text-sm">Loading media...</p>
              </div>

              <!-- Error state -->
              <div
                v-else-if="error"
                class="flex flex-col items-center gap-4 text-white max-w-md text-center px-4"
              >
                <ExclamationTriangleIcon class="w-12 h-12 text-yellow-400" />
                <p class="text-lg font-medium">{{ error }}</p>
                <div class="flex gap-2 mt-2">
                  <a
                    v-if="originalMediaUrl"
                    :href="originalMediaUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm transition-colors inline-flex items-center gap-2"
                    @click.stop
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    Open in new tab
                  </a>
                  <button
                    v-if="mediaUrls.length > 1 && currentIndex < mediaUrls.length - 1"
                    @click="handleNext"
                    class="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md text-sm transition-colors"
                  >
                    Next media →
                  </button>
                </div>
              </div>

              <!-- Media content -->
              <div
                v-else-if="currentMediaUrl"
                class="max-w-full max-h-full flex items-center justify-center w-full"
              >
                <!-- Image -->
                <ImageMedia
                  v-if="isImage"
                  :key="`img-${currentIndex}-${currentMediaUrl}`"
                  :src="currentMediaUrl"
                  :alt="title || 'Media'"
                  :viewer="true"
                  :lazy="false"
                  :placeholder="true"
                  container-class="max-w-full max-h-[calc(100vh-200px)] flex items-center justify-center"
                  image-class="max-w-full max-h-[calc(100vh-200px)] object-contain rounded-lg shadow-2xl cursor-pointer"
                  @load="handleImageLoad"
                  @error="handleImageError"
                  @click="handleOpenInNewTab"
                />

                <!-- Video -->
                <VideoMedia
                  v-else-if="isVideo"
                  ref="videoMediaRef"
                  :key="`video-${currentIndex}-${currentMediaUrl}`"
                  :src="currentMediaUrl"
                  :alt="title || 'Video'"
                  :autoplay="false"
                  :preload="'metadata'"
                  :show-controls="true"
                  :lazy="false"
                  :pause-on-unmount="true"
                  container-class="max-w-full max-h-[calc(100vh-200px)] flex items-center justify-center"
                  video-class="max-w-full max-h-[calc(100vh-200px)] rounded-lg shadow-2xl"
                  @play="handleVideoPlay"
                  @pause="handleVideoPause"
                  @error="handleVideoError"
                />

                <!-- Unknown type fallback -->
                <div
                  v-else
                  class="flex flex-col items-center gap-4 text-white max-w-md text-center px-4"
                >
                  <ExclamationTriangleIcon class="w-12 h-12 text-yellow-400" />
                  <p class="text-lg font-medium">Unknown media type</p>
                  <a
                    v-if="originalMediaUrl"
                    :href="originalMediaUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-md text-sm transition-colors"
                  >
                    Open in new tab
                  </a>
                </div>
              </div>

              <!-- Empty state -->
              <div
                v-else
                class="flex flex-col items-center gap-4 text-white max-w-md text-center px-4"
              >
                <ExclamationTriangleIcon class="w-12 h-12 text-gray-400" />
                <p class="text-lg font-medium">No media available</p>
              </div>
            </div>
          </div>

          <!-- Thumbnail strip (bottom) -->
          <div
            v-if="mediaUrls.length > 1"
            class="h-32 bg-black bg-opacity-50 border-t border-white border-opacity-10"
          >
            <ThumbnailStrip
              :media-urls="mediaUrls"
              :media-types="mediaTypeArray"
              :current-index="currentIndex"
              :thumbnail-size="100"
              @select="handleThumbnailSelect"
            />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import ImageMedia from './ImageMedia.vue'
import VideoMedia from './VideoMedia.vue'
import ThumbnailStrip from './ThumbnailStrip.vue'
import { useVideoManager } from '@/composables/useVideoManager'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mediaUrls: {
    type: Array,
    default: () => []
  },
  mediaType: {
    type: [Number, Array],
    default: null
  },
  currentIndex: {
    type: Number,
    default: 0
  },
  title: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'index-change'])

const loading = ref(false)
const error = ref(null)
const isHovered = ref(false)
const viewerRef = ref(null)
const videoMediaRef = ref(null)

// Video manager for single video playback
const { pauseAll } = useVideoManager()

// Helper function to get proxy URL
function getProxyUrl(originalUrl) {
  if (!originalUrl) return null

  // If URL is already a proxy URL, return as-is
  if (originalUrl.includes('/api/feed/media/proxy')) {
    return originalUrl
  }

  // Convert to proxy URL
  const encodedUrl = encodeURIComponent(originalUrl)
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  const backendUrl = isDev ? 'http://localhost:8000' : ''
  const proxyUrl = `${backendUrl}/api/feed/media/proxy?url=${encodedUrl}`
  return proxyUrl
}

// Computed: Media type as array
const mediaTypeArray = computed(() => {
  if (Array.isArray(props.mediaType)) {
    return props.mediaType
  }
  if (props.mediaType) {
    return props.mediaUrls.map(() => props.mediaType)
  }
  return props.mediaUrls.map(url => detectMediaTypeFromUrl(url))
})

// Computed current media URL (use proxy for external URLs)
const currentMediaUrl = computed(() => {
  if (!props.mediaUrls || props.mediaUrls.length === 0) {
    return null
  }
  const originalUrl =
    props.currentIndex >= 0 && props.currentIndex < props.mediaUrls.length
      ? props.mediaUrls[props.currentIndex]
      : props.mediaUrls[0] || null

  if (!originalUrl) return null

  // Use proxy URL to bypass CORS
  return getProxyUrl(originalUrl)
})

// Computed original media URL (for opening in new tab)
const originalMediaUrl = computed(() => {
  if (!props.mediaUrls || props.mediaUrls.length === 0) {
    return null
  }
  if (props.currentIndex >= 0 && props.currentIndex < props.mediaUrls.length) {
    return props.mediaUrls[props.currentIndex]
  }
  return props.mediaUrls[0] || null
})

// Detect media type from URL
function detectMediaTypeFromUrl(url) {
  if (!url) return 1 // Default to image

  const videoExtensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']
  const lowerUrl = url.toLowerCase()

  if (videoExtensions.some(ext => lowerUrl.includes(ext))) {
    return 2 // Video
  }

  return 1 // Image
}

// Computed: Current media type
const currentMediaType = computed(() => {
  if (Array.isArray(props.mediaType)) {
    return props.mediaType[props.currentIndex] || 1
  }
  return props.mediaType || detectMediaTypeFromUrl(originalMediaUrl.value)
})

const isImage = computed(() => {
  return currentMediaType.value === 1
})

const isVideo = computed(() => {
  return currentMediaType.value === 2
})

// Handle close
function handleClose() {
  // Pause any playing video
  pauseAll()
  videoMediaRef.value = null
  
  emit('update:modelValue', false)
  error.value = null
  loading.value = false
}

// Handle navigation
function handleNext() {
  if (props.currentIndex < props.mediaUrls.length - 1) {
    // Pause current video before navigating
    pauseAll()
    videoMediaRef.value = null
    
    const newIndex = props.currentIndex + 1
    emit('index-change', newIndex)
    resetMediaState()
  }
}

function handlePrevious() {
  if (props.currentIndex > 0) {
    // Pause current video before navigating
    pauseAll()
    videoMediaRef.value = null
    
    const newIndex = props.currentIndex - 1
    emit('index-change', newIndex)
    resetMediaState()
  }
}

// Handle thumbnail selection
function handleThumbnailSelect(index) {
  if (index !== props.currentIndex) {
    // Pause current video before navigating
    pauseAll()
    videoMediaRef.value = null
    
    emit('index-change', index)
    resetMediaState()
  }
}

// Reset media state when switching
function resetMediaState() {
  loading.value = true
  error.value = null
}

// Handle video play
function handleVideoPlay() {
  loading.value = false
  error.value = null
}

// Handle video pause
function handleVideoPause() {
  // Video paused
}

// Handle video error
function handleVideoError(event) {
  loading.value = false
  error.value = 'Failed to load video. The URL may be invalid or blocked.'
  console.error('[MediaGallery] Video error:', event)
}

// Handle image load
function handleImageLoad() {
  loading.value = false
  error.value = null
}

// Handle image error
function handleImageError(err) {
  loading.value = false
  error.value = 'Failed to load image. The URL may be invalid or blocked.'
  console.error('[MediaGallery] Image error:', err)
}

// Handle open in new tab
function handleOpenInNewTab() {
  if (originalMediaUrl.value) {
    window.open(originalMediaUrl.value, '_blank', 'noopener,noreferrer')
  }
}

// Keyboard navigation
function handleKeydown(event) {
  if (!props.modelValue) return

  switch (event.key) {
    case 'Escape':
      handleClose()
      break
    case 'ArrowLeft':
      event.preventDefault()
      handlePrevious()
      break
    case 'ArrowRight':
      event.preventDefault()
      handleNext()
      break
    case ' ': // Spacebar
      event.preventDefault()
      // Toggle play/pause for video
      if (isVideo.value && videoMediaRef.value) {
        const videoElement = videoMediaRef.value.videoRef || videoMediaRef.value.videoElement
        if (videoElement) {
          if (videoElement.paused) {
            videoElement.play().catch(err => console.error('[MediaGallery] Play error:', err))
          } else {
            videoElement.pause()
          }
        }
      }
      break
  }
}

// Watch for media URL changes to reset loading state
watch(
  () => originalMediaUrl.value,
  (newUrl, oldUrl) => {
    if (props.modelValue && newUrl && newUrl !== oldUrl) {
      resetMediaState()
    }
  }
)

// Watch for index changes to reset loading state
watch(
  () => props.currentIndex,
  (newIndex, oldIndex) => {
    if (props.modelValue && newIndex !== oldIndex) {
      resetMediaState()
    }
  }
)

// Initialize loading state when modal opens
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen && originalMediaUrl.value) {
      resetMediaState()
      
      // Set timeout to show error if media doesn't load within 10 seconds
      const timeoutId = setTimeout(() => {
        if (loading.value) {
          loading.value = false
          error.value = 'Media took too long to load. The URL may be invalid or blocked.'
        }
      }, 10000)

      // Clear timeout when modal closes
      return () => {
        clearTimeout(timeoutId)
      }
    } else {
      // Cleanup on close
      pauseAll()
      videoMediaRef.value = null
      error.value = null
      loading.value = false
    }
  },
  { immediate: true }
)

// Focus viewer on mount for keyboard navigation
onMounted(() => {
  if (props.modelValue && viewerRef.value) {
    nextTick(() => {
      viewerRef.value?.focus()
    })
  }
})
</script>

<style scoped>
.media-gallery-enter-active,
.media-gallery-leave-active {
  transition: opacity 0.3s ease;
}

.media-gallery-enter-from,
.media-gallery-leave-to {
  opacity: 0;
}

.media-gallery-enter-active .media-gallery-enter-active,
.media-gallery-leave-active .media-gallery-leave-active {
  transition: transform 0.3s ease;
}

.media-gallery-enter-from > div:last-child,
.media-gallery-leave-to > div:last-child {
  transform: scale(0.9);
}
</style>
