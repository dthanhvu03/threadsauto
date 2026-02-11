<template>
  <Transition
    enter-active-class="transition ease-out duration-300"
    enter-from-class="opacity-0 translate-x-full"
    enter-to-class="opacity-100 translate-x-0"
    leave-active-class="transition ease-in duration-200"
    leave-from-class="opacity-100 translate-x-0"
    leave-to-class="opacity-0 translate-x-full"
  >
    <div
      v-if="visible"
      :class="toastClasses"
      role="alert"
      class="flex items-start gap-3 p-4 rounded-lg shadow-lg min-w-[300px] max-w-[500px] pointer-events-auto"
    >
      <!-- Icon -->
      <component :is="iconComponent" :class="iconClasses" />

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <p v-if="title" :class="titleClasses">{{ title }}</p>
        <p :class="messageClasses">{{ message }}</p>
      </div>

      <!-- Close Button -->
      <button
        @click="handleDismiss"
        :class="closeButtonClasses"
        class="flex-shrink-0 p-1 rounded-md hover:bg-black/10 focus:outline-none focus:ring-2 focus:ring-offset-2"
        aria-label="Dismiss"
      >
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path
            fill-rule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/solid'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  },
  message: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: null
  },
  duration: {
    type: Number,
    default: 5000
  },
  id: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['dismiss'])

const visible = ref(false)
let timeoutId = null

const toastClasses = computed(() => {
  const base = 'bg-white border'
  const types = {
    success: 'border-green-200',
    error: 'border-red-200',
    warning: 'border-yellow-200',
    info: 'border-blue-200'
  }
  return `${base} ${types[props.type]}`
})

const iconComponent = computed(() => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon
  }
  return icons[props.type]
})

const iconClasses = computed(() => {
  const types = {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500'
  }
  return `w-5 h-5 flex-shrink-0 ${types[props.type]}`
})

const titleClasses = computed(() => {
  const types = {
    success: 'text-green-800',
    error: 'text-red-800',
    warning: 'text-yellow-800',
    info: 'text-blue-800'
  }
  return `text-sm font-semibold ${types[props.type]}`
})

const messageClasses = computed(() => {
  const types = {
    success: 'text-green-700',
    error: 'text-red-700',
    warning: 'text-yellow-700',
    info: 'text-blue-700'
  }
  return `text-sm ${props.title ? 'mt-1' : ''} ${types[props.type]}`
})

const closeButtonClasses = computed(() => {
  const types = {
    success: 'text-green-500 hover:text-green-700 focus:ring-green-500',
    error: 'text-red-500 hover:text-red-700 focus:ring-red-500',
    warning: 'text-yellow-500 hover:text-yellow-700 focus:ring-yellow-500',
    info: 'text-blue-500 hover:text-blue-700 focus:ring-blue-500'
  }
  return types[props.type]
})

const handleDismiss = () => {
  visible.value = false
  if (timeoutId) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
  setTimeout(() => {
    emit('dismiss', props.id)
  }, 200) // Wait for transition
}

onMounted(() => {
  // Trigger enter animation
  setTimeout(() => {
    visible.value = true
  }, 10)

  // Auto-dismiss if duration > 0
  if (props.duration > 0) {
    timeoutId = setTimeout(() => {
      handleDismiss()
    }, props.duration)
  }
})

onUnmounted(() => {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
})
</script>
