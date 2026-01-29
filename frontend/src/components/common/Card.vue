<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="px-3 md:px-4 lg:px-6 py-3 md:py-4 border-b border-gray-200 bg-gray-50">
      <slot name="header" />
    </div>
    <div :class="bodyClasses">
      <slot />
    </div>
    <div v-if="$slots.footer" class="px-3 md:px-4 lg:px-6 py-3 md:py-4 border-t border-gray-200 bg-gray-50">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value)
  },
  shadow: {
    type: Boolean,
    default: true
  }
})

const cardClasses = computed(() => {
  // Border Radius: Mobile rounded-lg (8px), Tablet rounded-lg (8px), Desktop rounded-xl (12px)
  // Shadow: Mobile shadow-sm, Tablet shadow, Desktop shadow-md
  const shadowClass = props.shadow 
    ? 'shadow-sm md:shadow lg:shadow-md' 
    : ''
  return [
    'bg-white rounded-lg lg:rounded-xl border border-gray-200',
    shadowClass
  ].filter(Boolean).join(' ')
})

const bodyClasses = computed(() => {
  // Padding: Mobile p-3 (12px), Tablet p-4 (16px), Desktop p-6 (24px)
  const paddings = {
    none: '',
    sm: 'p-2 md:p-3 lg:p-4',      // 8px / 12px / 16px
    md: 'p-3 md:p-4 lg:p-6',      // 12px / 16px / 24px
    lg: 'p-4 md:p-6 lg:p-8'       // 16px / 24px / 32px
  }
  return paddings[props.padding]
})
</script>
