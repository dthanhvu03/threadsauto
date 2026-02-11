<template>
  <div
    class="group bg-white border border-gray-200 rounded-lg hover:shadow-md transition-all duration-200 overflow-hidden"
    :class="index % 2 === 0 ? '' : 'bg-gray-50/30'"
  >
    <div class="flex gap-4 p-4">
      <!-- User Section (left, fixed width) -->
      <div class="flex-shrink-0 w-32">
        <div class="flex items-center gap-3">
          <!-- Avatar -->
          <div class="relative flex-shrink-0">
            <div class="relative w-12 h-12">
              <ImageMedia
                v-if="item.user_id"
                :src="getAvatarUrl(item.user_id, 'thumbnail')"
                :alt="item.username"
                :width="48"
                :height="48"
                size="thumbnail"
                :lazy="true"
                :placeholder="true"
                container-class="w-12 h-12 rounded-full border-2 border-white shadow-md ring-1 ring-gray-100"
                image-class="rounded-full"
              />
              <div
                v-else
                class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm border-2 border-white shadow-md ring-1 ring-gray-100"
              >
                {{ item.user_display_name?.charAt(0) || item.username?.charAt(0) || '?' }}
              </div>
              <!-- Verified Badge Overlay -->
              <div
                v-if="item.is_verified"
                class="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-white rounded-full flex items-center justify-center shadow-sm border border-white"
                title="Verified Account"
              >
                <svg class="w-2.5 h-2.5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
          <!-- User Info -->
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-1.5">
              <span class="font-semibold text-gray-900 truncate text-sm">@{{ item.username }}</span>
            </div>
            <div v-if="item.user_display_name" class="text-xs text-gray-600 truncate">
              {{ item.user_display_name }}
            </div>
            <div class="text-xs text-gray-500 mt-0.5">
              {{ formatTimeAgo(item.timestamp_iso || new Date(item.timestamp * 1000).toISOString()) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Content Section (center-left, flexible) -->
      <div class="flex-1 min-w-0">
        <div class="relative">
          <!-- Text Content -->
          <div class="mb-2">
            <p
              :class="[
                'text-sm text-gray-900 leading-relaxed',
                isExpanded ? '' : 'line-clamp-3'
              ]"
            >
              {{ item.text || 'No text content' }}
            </p>
            <!-- Expand/Collapse Button -->
            <button
              v-if="needsExpansion"
              @click="toggleExpand"
              class="mt-1 text-xs text-blue-600 hover:text-blue-700 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              :aria-label="isExpanded ? 'Collapse content' : 'Expand content'"
            >
              {{ isExpanded ? 'Show less' : 'Show more' }}
            </button>
          </div>
          
          <!-- Hashtags & Mentions -->
          <div v-if="(item.hashtags && item.hashtags.length > 0) || (item.mentions && item.mentions.length > 0)" class="flex flex-wrap gap-1.5 mt-2">
            <span
              v-for="hashtag in (item.hashtags || []).slice(0, 3)"
              :key="hashtag"
              class="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full font-medium border border-blue-200"
            >
              <span>#</span>{{ hashtag }}
            </span>
            <span
              v-for="mention in (item.mentions || []).slice(0, 2)"
              :key="mention"
              class="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full font-medium border border-purple-200"
            >
              <span>@</span>{{ mention }}
            </span>
          </div>
        </div>
      </div>

      <!-- Media Section (center-right) -->
      <div class="flex-shrink-0 w-32 flex items-center justify-center">
        <div v-if="item.media_count && item.media_count > 0" class="relative">
          <div 
            @click="handleViewMedia"
            class="group/media relative cursor-pointer transition-all duration-200 hover:scale-105"
            role="button"
            tabindex="0"
            @keydown.enter="handleViewMedia"
            @keydown.space.prevent="handleViewMedia"
            :aria-label="item.media_count > 1 ? `View ${item.media_count} media` : 'View media'"
          >
            <!-- Thumbnail Preview (120x120px) -->
            <div class="relative w-[120px] h-[120px] rounded-lg overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 border-2 border-gray-200 shadow-md hover:shadow-xl transition-all duration-200">
              <!-- Image Media -->
              <ImageMedia
                v-if="item.media_type !== 2"
                :src="getMediaUrl(item.post_id, 0, 'thumbnail')"
                :alt="`Media preview for ${item.username}`"
                :width="120"
                :height="120"
                size="thumbnail"
                :lazy="true"
                :placeholder="true"
                container-class="absolute inset-0"
                image-class="rounded-lg object-cover"
              />
              
              <!-- Video Media (with poster) -->
              <VideoMedia
                v-else
                :src="getMediaUrl(item.post_id, 0, 'full')"
                :poster="getMediaUrl(item.post_id, 0, 'thumbnail')"
                :alt="`Video preview for ${item.username}`"
                :width="120"
                :height="120"
                :preload="'none'"
                :autoplay="false"
                :show-controls="false"
                :lazy="true"
                :placeholder="true"
                container-class="absolute inset-0"
              />
              
              <!-- Media Count Badge -->
              <div 
                v-if="item.media_count > 1"
                class="absolute top-1.5 right-1.5 px-2 py-0.5 bg-black/80 backdrop-blur-sm text-white text-xs font-bold rounded-md shadow-lg z-10"
              >
                {{ item.media_count }}
              </div>
              
              <!-- Video Play Icon Overlay -->
              <div
                v-if="item.media_type === 2"
                class="absolute bottom-1.5 left-1.5 p-1.5 bg-black/70 backdrop-blur-sm rounded-full z-10"
              >
                <svg 
                  class="w-4 h-4 text-white" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="flex items-center justify-center">
          <span class="text-gray-300 text-sm">—</span>
        </div>
      </div>

      <!-- Engagement & Actions Section (right) -->
      <div class="flex-shrink-0 w-40 flex flex-col items-end gap-3">
        <!-- Engagement Metrics (compact horizontal) -->
        <div class="flex items-center gap-3 text-gray-600">
          <div class="flex items-center gap-1" title="Likes">
            <svg class="w-3.5 h-3.5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd" />
            </svg>
            <span class="text-xs font-medium">{{ formatNumber(item.like_count) }}</span>
          </div>
          <div class="flex items-center gap-1" title="Replies">
            <svg class="w-3.5 h-3.5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span class="text-xs font-medium">{{ formatNumber(item.reply_count) }}</span>
          </div>
          <div class="flex items-center gap-1" title="Reposts">
            <svg class="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span class="text-xs font-medium">{{ formatNumber(item.repost_count) }}</span>
          </div>
          <div v-if="item.view_count" class="flex items-center gap-1" title="Views">
            <svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span class="text-xs font-medium">{{ formatNumber(item.view_count) }}</span>
          </div>
        </div>

        <!-- Actions (hover-revealed) -->
        <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            @click.stop="$emit('like', item.post_id)"
            class="p-1.5 rounded-md text-red-500 hover:bg-red-50 hover:text-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
            title="Like"
            aria-label="Like post"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>
          <button
            @click.stop="$emit('comment', item)"
            class="p-1.5 rounded-md text-blue-500 hover:bg-blue-50 hover:text-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Comment"
            aria-label="Comment on post"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </button>
          <button
            @click.stop="$emit('repost', item.post_id)"
            class="p-1.5 rounded-md text-green-500 hover:bg-green-50 hover:text-green-700 transition-colors focus:outline-none focus:ring-2 focus:ring-green-500"
            title="Repost"
            aria-label="Repost"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <a
            :href="item.post_url"
            target="_blank"
            rel="noopener noreferrer"
            class="p-1.5 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
            title="View on Threads"
            aria-label="View post on Threads"
            @click.stop
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ImageMedia from '@/components/common/ImageMedia.vue'
import VideoMedia from '@/components/common/VideoMedia.vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 0
  },
  getAvatarUrl: {
    type: Function,
    required: true
  },
  getMediaUrl: {
    type: Function,
    required: true
  },
  formatTimeAgo: {
    type: Function,
    required: true
  },
  formatNumber: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['view-media', 'like', 'comment', 'repost'])

const isExpanded = ref(false)

// Check if content needs expansion (rough estimate: more than 3 lines)
const needsExpansion = computed(() => {
  const text = props.item.text || ''
  // Rough estimate: ~80 characters per line, so 3 lines = ~240 chars
  return text.length > 240
})

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleViewMedia = () => {
  if (props.item.media_count && props.item.media_count > 0) {
    emit('view-media', props.item)
  }
}
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
