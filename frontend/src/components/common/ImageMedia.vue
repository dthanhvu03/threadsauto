<template>
  <div
    ref="containerRef"
    :style="containerStyle"
    class="relative overflow-hidden"
    :class="containerClass"
  >
    <!-- Skeleton Placeholder -->
    <div
      v-if="showPlaceholder && (state === 'loading' || state === 'idle')"
      :style="skeletonStyle"
      :class="[
        'absolute inset-0 bg-gradient-to-br animate-pulse',
        viewer
          ? 'from-gray-800 via-gray-700 to-gray-800 flex items-center justify-center'
          : 'from-gray-200 via-gray-100 to-gray-200'
      ]"
      :aria-label="`Loading ${alt}`"
    >
      <!-- Viewer context: larger centered spinner -->
      <div
        v-if="viewer"
        class="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin"
      />
    </div>

    <!-- Image -->
    <img
      v-if="shouldLoad && state !== 'error'"
      ref="imageRef"
      :src="imageSrc"
      :alt="alt"
      :width="width"
      :height="height"
      :style="imageStyle"
      :class="imageClass"
      :loading="lazy ? 'lazy' : 'eager'"
      decoding="async"
      @load="handleLoad"
      @error="handleError"
    />

    <!-- Error Fallback -->
    <div
      v-if="state === 'error'"
      :style="errorStyle"
      class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200"
      :aria-label="`Failed to load ${alt}`"
    >
      <svg
        class="text-gray-400"
        :style="{ width: `${Math.min(width, height) * 0.4}px`, height: `${Math.min(width, height) * 0.4}px` }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useIntersectionObserver } from '@/composables/useIntersectionObserver'

const props = defineProps({
  /**
   * Image source URL.
   */
  src: {
    type: String,
    required: true
  },
  /**
   * Alt text for accessibility.
   */
  alt: {
    type: String,
    default: ''
  },
  /**
   * Fixed width in pixels (prevents layout shift).
   */
  width: {
    type: [Number, String],
    default: null
  },
  /**
   * Fixed height in pixels (prevents layout shift).
   */
  height: {
    type: [Number, String],
    default: null
  },
  /**
   * Size variant: 'thumbnail' or 'full'.
   */
  size: {
    type: String,
    default: 'full',
    validator: (value) => ['thumbnail', 'full'].includes(value)
  },
  /**
   * Enable lazy loading with IntersectionObserver.
   */
  lazy: {
    type: Boolean,
    default: true
  },
  /**
   * Show skeleton placeholder while loading.
   */
  placeholder: {
    type: Boolean,
    default: true
  },
  /**
   * Viewer context: disable lazy loading and optimize for viewer.
   */
  viewer: {
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
   * Additional CSS classes for image.
   */
  imageClass: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['load', 'error'])

// State: 'idle' | 'loading' | 'loaded' | 'error'
const state = ref('idle')
const containerRef = ref(null)
const imageRef = ref(null)

// IntersectionObserver for lazy loading
const { isIntersecting, observe, unobserve } = useIntersectionObserver({
  rootMargin: '50px',
  threshold: 0.1,
  once: true
})

// Computed: Should load image?
const shouldLoad = computed(() => {
  // In viewer context, always load immediately (no lazy loading)
  if (props.viewer) return true
  if (!props.lazy) return true
  return isIntersecting.value || state.value === 'loaded'
})

// Computed: Show placeholder?
const showPlaceholder = computed(() => {
  return props.placeholder && (state.value === 'loading' || state.value === 'idle')
})

// Computed: Image source (empty until should load)
const imageSrc = computed(() => {
  if (!shouldLoad.value) return ''
  return props.src
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

// Computed: Skeleton style (same as container)
const skeletonStyle = computed(() => {
  return containerStyle.value
})

// Computed: Image style
const imageStyle = computed(() => {
  const style = {
    width: '100%',
    height: '100%',
    objectFit: props.viewer ? 'contain' : 'cover',
    transition: 'opacity 0.3s ease-in-out'
  }

  // Fade in when loaded
  if (state.value === 'loaded') {
    style.opacity = '1'
  } else {
    style.opacity = '0'
  }

  return style
})

// Computed: Error style (same as container)
const errorStyle = computed(() => {
  return containerStyle.value
})

// Handle image load
const handleLoad = () => {
  state.value = 'loaded'
  emit('load')
  if (props.lazy) {
    unobserve()
  }
}

// Handle image error
const handleError = () => {
  state.value = 'error'
  console.warn('[ImageMedia] Failed to load image:', props.src)
  emit('error', new Error('Failed to load image'))
  if (props.lazy) {
    unobserve()
  }
}

// Watch for intersection changes
watch(isIntersecting, (newValue) => {
  if (newValue && state.value === 'idle') {
    state.value = 'loading'
  }
})

// Watch for src changes (reset state)
watch(() => props.src, () => {
  state.value = 'idle'
  if (!props.lazy) {
    state.value = 'loading'
  }
})

// Setup IntersectionObserver
onMounted(() => {
  // In viewer context, always load immediately
  if (props.viewer) {
    state.value = 'loading'
  } else if (props.lazy && containerRef.value) {
    observe(containerRef.value)
  } else {
    // Load immediately if not lazy
    state.value = 'loading'
  }
})

onUnmounted(() => {
  unobserve()
})
</script>

<style scoped>
/* Smooth fade-in animation */
img {
  will-change: opacity;
}
</style>
