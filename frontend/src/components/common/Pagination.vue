<template>
  <div v-if="totalPages > 1 || showPageSize" class="flex flex-col gap-3 md:gap-4 py-3 md:py-4 border-t border-gray-200">
    <!-- Top Row: Page Size Selector and Page Info -->
    <div class="flex flex-col md:flex-row items-center justify-between gap-3 md:gap-4">
      <!-- Page Size Selector -->
      <div v-if="showPageSize" class="flex items-center gap-2 w-full sm:w-auto">
        <label class="text-xs md:text-sm text-gray-700 whitespace-nowrap">Items per page:</label>
        <select
          :value="pageSize"
          @change="handlePageSizeChange($event.target.value)"
          class="rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm min-h-[44px] md:min-h-[38px] px-3 py-2.5 md:py-2 flex-1 md:flex-none"
        >
          <option v-for="size in pageSizeOptions" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
      </div>

      <!-- Page Info -->
      <div class="text-xs md:text-sm text-gray-700 text-center md:text-left w-full md:w-auto">
        Showing {{ startItem }} to {{ endItem }} of {{ total }} results
      </div>
    </div>

    <!-- Bottom Row: Page Navigation -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-1 md:gap-2 overflow-x-auto">
      <!-- Previous Button -->
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        :class="[
          'px-3 py-2.5 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-colors min-h-[44px] md:min-h-[38px] whitespace-nowrap flex-shrink-0',
          currentPage === 1
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
        ]"
      >
        Previous
      </button>

      <!-- Page Numbers -->
      <div class="flex items-center gap-1 md:gap-2 overflow-x-auto">
        <button
          v-for="page in visiblePages"
          :key="page"
          @click="goToPage(page)"
          :class="[
            'px-3 py-2.5 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-colors min-w-[44px] md:min-w-[38px] min-h-[44px] md:min-h-[38px] flex-shrink-0',
            page === currentPage
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          ]"
        >
          {{ page }}
        </button>
      </div>

      <!-- Next Button -->
      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        :class="[
          'px-3 py-2.5 md:py-2 rounded-lg text-xs md:text-sm font-medium transition-colors min-h-[44px] md:min-h-[38px] whitespace-nowrap flex-shrink-0',
          currentPage === totalPages
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
        ]"
      >
        Next
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    required: true,
    default: 1
  },
  pageSize: {
    type: Number,
    required: true,
    default: 20
  },
  total: {
    type: Number,
    required: true,
    default: 0
  },
  pageSizeOptions: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  showPageSize: {
    type: Boolean,
    default: true
  },
  maxVisiblePages: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits(['page-change', 'page-size-change'])

const totalPages = computed(() => {
  return Math.ceil(props.total / props.pageSize)
})

const startItem = computed(() => {
  if (props.total === 0) return 0
  return (props.currentPage - 1) * props.pageSize + 1
})

const endItem = computed(() => {
  const end = props.currentPage * props.pageSize
  return end > props.total ? props.total : end
})

const visiblePages = computed(() => {
  const pages = []
  const maxPages = props.maxVisiblePages
  const current = props.currentPage
  const total = totalPages.value

  if (total <= maxPages) {
    // Show all pages if total pages is less than max
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // Calculate start and end page numbers
    let start = Math.max(1, current - Math.floor(maxPages / 2))
    let end = Math.min(total, start + maxPages - 1)

    // Adjust start if we're near the end
    if (end - start < maxPages - 1) {
      start = Math.max(1, end - maxPages + 1)
    }

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
  }

  return pages
})

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value && page !== props.currentPage) {
    emit('page-change', page)
  }
}

const handlePageSizeChange = (newSize) => {
  const size = parseInt(newSize, 10)
  if (size !== props.pageSize) {
    emit('page-size-change', size)
  }
}
</script>
