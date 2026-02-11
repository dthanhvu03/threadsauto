<template>
  <div
    ref="containerRef"
    :style="containerStyle"
    class="relative overflow-hidden bg-black"
    :class="containerClass"
  >
    <!-- Poster Image (shown initially) -->
    <ImageMedia
      v-if="showPoster && !isPlaying"
      :src="poster"
      :alt="`Video poster: ${alt}`"
      :width="width"
      :height="height"
      size="thumbnail"
      :lazy="lazy"
      :placeholder="placeholder"
      class="absolute inset-0"
    />

    <!-- Play Button Overlay -->
    <button
      v-if="showPoster && !isPlaying"
      @click="handlePlayClick"
      class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 hover:bg-opacity-40 transition-all duration-200 z-10 group"
      :aria-label="`Play video: ${alt}`"
    >
      <div class="w-16 h-16 bg-white bg-opacity-90 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200">
        <svg class="w-8 h-8 text-gray-900 ml-1" fill="currentColor" viewBox="0 0 20 20">
          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
        </svg>
      </div>
    </button>

    <!-- Video Element -->
    <video
      v-if="shouldLoadVideo"
      ref="videoRef"
      :src="videoSrc"
      :width="width"
      :height="height"
      :style="videoStyle"
      :class="videoClass"
      :preload="preload"
      :autoplay="autoplay"
      :controls="showControls"
      :poster="poster"
      :muted="muted"
      @loadedmetadata="handleMetadataLoaded"
      @play="handlePlay"
      @pause="handlePause"
      @ended="handleEnded"
      @error="handleError"
    />

    <!-- Loading State (when preparing video) -->
    <div
      v-if="state === 'preparing'"
      class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50"
    >
      <div class="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Error Fallback -->
    <div
      v-if="state === 'error'"
      :style="errorStyle"
      class="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200"
      :aria-label="`Failed to load video: ${alt}`"
    >
      <svg
        class="text-gray-400 mb-2"
        :style="{ width: `${Math.min(width, height) * 0.3}px`, height: `${Math.min(width, height) * 0.3}px` }"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
      </svg>
      <span class="text-xs text-gray-500">Video unavailable</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useIntersectionObserver } from '@/composables/useIntersectionObserver'
import { useVideoManager } from '@/composables/useVideoManager'
import ImageMedia from './ImageMedia.vue'

const props = defineProps({
  /**
   * Video source URL.
   */
  src: {
    type: String,
    required: true
  },
  /**
   * Poster image URL (thumbnail).
   */
  poster: {
    type: String,
    default: ''
  },
  /**
   * Alt text for accessibility.
   */
  alt: {
    type: String,
    default: ''
  },
  /**
   * Fixed width in pixels.
   */
  width: {
    type: [Number, String],
    default: null
  },
  /**
   * Fixed height in pixels.
   */
  height: {
    type: [Number, String],
    default: null
  },
  /**
   * Autoplay video.
   */
  autoplay: {
    type: Boolean,
    default: false
  },
  /**
   * Preload strategy: 'none' | 'metadata' | 'auto'.
   */
  preload: {
    type: String,
    default: 'none',
    validator: (value) => ['none', 'metadata', 'auto'].includes(value)
  },
  /**
   * Show video controls.
   */
  showControls: {
    type: Boolean,
    default: true
  },
  /**
   * Lazy load video metadata.
   */
  lazy: {
    type: Boolean,
    default: true
  },
  /**
   * Show placeholder while loading.
   */
  placeholder: {
    type: Boolean,
    default: true
  },
  /**
   * Mute video by default.
   */
  muted: {
    type: Boolean,
    default: false
  },
  /**
   * Additional CSS classes for container.
   */
  containerClass: {
    type: String,
    default: ''
  },
  /**
   * Additional CSS classes for video.
   */
  videoClass: {
    type: String,
    default: ''
  },
  /**
   * Pause video when component unmounts.
   */
  pauseOnUnmount: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['play', 'pause', 'ended', 'error'])

// State: 'idle' | 'preparing' | 'ready' | 'playing' | 'paused' | 'error'
const state = ref('idle')
const containerRef = ref(null)
const videoRef = ref(null)

// Expose video ref for parent components
defineExpose({
  videoRef,
  videoElement: computed(() => videoRef.value)
})
const videoId = ref(`video-${Math.random().toString(36).substr(2, 9)}`)

// Video manager
const { playVideo, registerVideo, unregisterVideo, isPlaying } = useVideoManager()

// IntersectionObserver for lazy loading
const { isIntersecting, observe, unobserve } = useIntersectionObserver({
  rootMargin: '50px',
  threshold: 0.1,
  once: false // Keep observing to pause when leaving viewport
})

// Computed: Show poster?
const showPoster = computed(() => {
  return props.poster && (state.value === 'idle' || state.value === 'preparing' || (!isPlaying.value && state.value !== 'error'))
})

// Computed: Should load video?
const shouldLoadVideo = computed(() => {
  // Load video if:
  // 1. Not lazy, OR
  // 2. Intersecting viewport, OR
  // 3. Already playing/prepared
  if (!props.lazy) return true
  if (isIntersecting.value) return true
  if (state.value === 'ready' || state.value === 'playing' || state.value === 'paused') return true
  return false
})

// Computed: Video source (empty until should load)
const videoSrc = computed(() => {
  if (!shouldLoadVideo.value) return ''
  return props.src
})

// Computed: Is currently playing?
const isCurrentlyPlaying = computed(() => {
  return isPlaying(videoId.value)
})

// Computed: Container style
const containerStyle = computed(() => {
  const style = {}
  if (props.width) {
    style.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  }
  if (props.height) {
    style.height = typeof props.height === 'number' ? `${props.height}px` : props.height
  }
  return style
})

// Computed: Video style
const videoStyle = computed(() => {
  return {
    width: '100%',
    height: '100%',
    objectFit: 'contain'
  }
})

// Computed: Error style
const errorStyle = computed(() => {
  return containerStyle.value
})

// Handle play click
const handlePlayClick = async () => {
  if (!videoRef.value) {
    // Load video first
    state.value = 'preparing'
    return
  }

  try {
    playVideo(videoId.value, videoRef.value)
    state.value = 'playing'
    emit('play')
  } catch (error) {
    console.error('[VideoMedia] Failed to play video:', error)
    state.value = 'error'
    emit('error', error)
  }
}

// Handle metadata loaded
const handleMetadataLoaded = () => {
  state.value = 'ready'
  
  // Register video with manager
  if (videoRef.value) {
    registerVideo(videoId.value, videoRef.value)
  }

  // Autoplay if requested
  if (props.autoplay && videoRef.value) {
    handlePlayClick()
  }
}

// Handle play event
const handlePlay = () => {
  state.value = 'playing'
  emit('play')
}

// Handle pause event
const handlePause = () => {
  if (state.value === 'playing') {
    state.value = 'paused'
    emit('pause')
  }
}

// Handle ended event
const handleEnded = () => {
  state.value = 'ready'
  emit('ended')
}

// Handle error
const handleError = (event) => {
  state.value = 'error'
  console.error('[VideoMedia] Video error:', event)
  emit('error', event)
}

// Watch for intersection changes
watch(isIntersecting, (newValue) => {
  if (!newValue && videoRef.value && !videoRef.value.paused) {
    // Pause when leaving viewport
    videoRef.value.pause()
    state.value = 'paused'
  } else if (newValue && state.value === 'idle' && props.preload !== 'none') {
    // Prepare video when entering viewport (if preload allows)
    state.value = 'preparing'
  }
})

// Watch for src changes (reset state)
watch(() => props.src, () => {
  state.value = 'idle'
  if (videoRef.value) {
    videoRef.value.load()
  }
})

// Setup IntersectionObserver
onMounted(() => {
  if (props.lazy && containerRef.value) {
    observe(containerRef.value)
  } else {
    // Load immediately if not lazy
    if (props.preload !== 'none') {
      state.value = 'preparing'
    }
  }
})

onUnmounted(() => {
  unobserve()
  
  // Pause video on unmount if enabled
  if (props.pauseOnUnmount && videoRef.value && !videoRef.value.paused) {
    videoRef.value.pause()
  }
  
  unregisterVideo(videoId.value)
})
</script>

<style scoped>
video {
  display: block;
}
</style>
