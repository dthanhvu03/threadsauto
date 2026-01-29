<template>
  <span :class="badgeClasses">
    <span v-if="dot" :class="dotClasses"></span>
    <slot>
      <span v-if="variant === 'count' && count !== null">{{ count }}</span>
      <span v-else>{{ label }}</span>
    </slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'success', 'warning', 'error', 'info', 'new', 'count'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  dot: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: null
  },
  count: {
    type: Number,
    default: null
  }
})

const badgeClasses = computed(() => {
  // "new" variant uses rounded-md instead of rounded-full
  const base = props.variant === 'new' 
    ? 'inline-flex items-center font-medium rounded-md'
    : 'inline-flex items-center font-medium rounded-full'
  
  const sizes = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-0.5 text-xs',
    lg: 'px-2.5 py-1 text-sm'
  }
  
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
    new: 'bg-blue-50 text-blue-600',
    count: 'bg-gray-100 text-gray-800'
  }
  
  return `${base} ${sizes[props.size]} ${variants[props.variant]}`
})

const dotClasses = computed(() => {
  const base = 'w-1.5 h-1.5 rounded-full mr-1.5'
  const variants = {
    default: 'bg-gray-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    info: 'bg-blue-500'
  }
  return `${base} ${variants[props.variant]}`
})
</script>
