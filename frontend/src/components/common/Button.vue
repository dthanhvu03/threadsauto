<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="mr-2">
      <LoadingSpinner size="sm" />
    </span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'success', 'outline'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    default: 'button'
  },
  fullWidth: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const buttonClasses = computed(() => {
  const base = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1'
  
  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500 disabled:bg-gray-400',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500 disabled:bg-gray-100',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:bg-gray-400',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500 disabled:bg-gray-400',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500 disabled:border-gray-200'
  }
  
  const sizes = {
    // Small: Mobile 44px, Tablet 36px, Desktop 32px
    sm: 'px-3 py-2.5 md:py-2 lg:py-1.5 text-sm min-h-[44px] md:min-h-[36px] lg:min-h-[32px]',
    // Medium: Mobile 44px, Tablet 40px, Desktop 40px
    md: 'px-4 py-3 md:py-2.5 lg:py-2 text-sm md:text-sm lg:text-base min-h-[44px] md:min-h-[40px] lg:min-h-[40px]',
    // Large: Mobile 48px, Tablet 44px, Desktop 44px
    lg: 'px-5 md:px-6 py-3.5 md:py-3 lg:py-3 text-base md:text-base lg:text-lg min-h-[48px] md:min-h-[44px] lg:min-h-[44px]'
  }
  
  return [
    base,
    variants[props.variant],
    sizes[props.size],
    props.fullWidth && 'w-full',
    (props.disabled || props.loading) && 'cursor-not-allowed opacity-50'
  ].filter(Boolean).join(' ')
})
</script>
