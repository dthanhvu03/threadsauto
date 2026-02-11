<template>
  <div
    ref="containerRef"
    class="thumbnail-container relative w-full h-full overflow-x-auto overflow-y-hidden"
    @scroll="handleScroll"
  >
    <div
      ref="scrollContainerRef"
      class="flex gap-3 px-4 py-3 items-center h-full"
      :style="{ minWidth: 'fit-content' }"
    >
      <button
        v-for="(url, index) in mediaUrls"
        :key="`thumb-${index}`"
        @click="handleSelect(index)"
        :class="[
          'flex-shrink-0 relative rounded-lg overflow-hidden border-2 transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black',
          index === currentIndex
            ? 'border-white scale-105 shadow-lg'
            : 'border-transparent hover:border-gray-400 hover:scale-102'
        ]"
        :style="thumbnailStyle"
        :aria-label="`Select media ${index + 1}`"
      >
        <!-- Thumbnail Image -->
        <ImageMedia
          :src="getProxyUrl(getThumbnailUrl(url, index))"
          :alt="`Thumbnail ${index + 1}`"
          :width="thumbnailSize"
          :height="thumbnailSize"
          size="thumbnail"
          :lazy="true"
          :placeholder="true"
          container-class="w-full h-full"
          image-class="object-cover"
        />

        <!-- Video Indicator Overlay -->
        <div
          v-if="isVideoType(index)"
          class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30"
        >
          <svg
            class="w-6 h-6 text-white"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
          </svg>
        </div>

        <!-- Selected Indicator -->
        <div
          v-if="index === currentIndex"
          class="absolute inset-0 border-2 border-white rounded-lg pointer-events-none"
        />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import ImageMedia from './ImageMedia.vue'

const props = defineProps({
  /**
   * Array of media URLs.
   */
  mediaUrls: {
    type: Array,
    required: true,
    default: () => []
  },
  /**
   * Array of media types (1=image, 2=video).
   * Can be single number or array matching mediaUrls length.
   */
  mediaTypes: {
    type: [Number, Array],
    default: null
  },
  /**
   * Currently selected index.
   */
  currentIndex: {
    type: Number,
    required: true,
    default: 0
  },
  /**
   * Optional array of thumbnail URLs (if different from mediaUrls).
   */
  thumbnailUrls: {
    type: Array,
    default: null
  },
  /**
   * Thumbnail size in pixels.
   */
  thumbnailSize: {
    type: Number,
    default: 100
  }
})

const emit = defineEmits(['select'])

const containerRef = ref(null)
const scrollContainerRef = ref(null)
const isScrolling = ref(false)

// Computed: Thumbnail style
const thumbnailStyle = computed(() => ({
  width: `${props.thumbnailSize}px`,
  height: `${props.thumbnailSize}px`
}))

// Helper: Get media type for index
function getMediaType(index) {
  if (Array.isArray(props.mediaTypes)) {
    return props.mediaTypes[index] || 1 // Default to image
  }
  return props.mediaTypes || 1
}

// Helper: Check if media type is video
function isVideoType(index) {
  return getMediaType(index) === 2
}

// Helper: Get thumbnail URL (use thumbnailUrls if provided, otherwise use mediaUrls)
function getThumbnailUrl(mediaUrl, index) {
  if (props.thumbnailUrls && props.thumbnailUrls[index]) {
    return props.thumbnailUrls[index]
  }
  return mediaUrl
}

// Helper: Get proxy URL (same logic as MediaGallery)
function getProxyUrl(originalUrl) {
  if (!originalUrl) return null
  
  if (originalUrl.includes('/api/feed/media/proxy')) {
    return originalUrl
  }
  
  const encodedUrl = encodeURIComponent(originalUrl)
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  const backendUrl = isDev ? 'http://localhost:8000' : ''
  return `${backendUrl}/api/feed/media/proxy?url=${encodedUrl}`
}

// Handle thumbnail selection
function handleSelect(index) {
  if (index !== props.currentIndex) {
    emit('select', index)
  }
}

// Handle scroll (debounce auto-scroll to prevent conflicts)
function handleScroll() {
  isScrolling.value = true
  setTimeout(() => {
    isScrolling.value = false
  }, 150)
}

// Auto-center selected thumbnail
async function centerSelectedThumbnail() {
  if (!containerRef.value || !scrollContainerRef.value || isScrolling.value) {
    return
  }

  await nextTick()

  const buttons = scrollContainerRef.value.querySelectorAll('button')
  const selectedButton = buttons[props.currentIndex]

  if (selectedButton) {
    selectedButton.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center'
    })
  }
}

// Watch for currentIndex changes to auto-center
watch(() => props.currentIndex, () => {
  // Small delay to ensure DOM is updated
  setTimeout(() => {
    centerSelectedThumbnail()
  }, 100)
})

// Center on mount if currentIndex is set
onMounted(() => {
  if (props.currentIndex >= 0) {
    setTimeout(() => {
      centerSelectedThumbnail()
    }, 200)
  }
})
</script>

<style scoped>
/* Smooth scrolling */
.thumbnail-container {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
}

.thumbnail-container::-webkit-scrollbar {
  height: 6px;
}

.thumbnail-container::-webkit-scrollbar-track {
  background: transparent;
}

.thumbnail-container::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.thumbnail-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.5);
}
</style>
