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
  // Design System: background #F8FAFC, border-radius 12px, shadow-md, transition all 200ms ease, cursor pointer from MASTER.md
  const shadowClass = props.shadow 
    ? 'shadow-md hover:shadow-lg' 
    : ''
  return [
    'bg-background rounded-xl border border-border',
    'transition-all duration-200 cursor-pointer',
    'hover:-translate-y-0.5', // translateY(-2px) = -translate-y-0.5
    shadowClass
  ].filter(Boolean).join(' ')
})

const bodyClasses = computed(() => {
  // Design System: padding 24px (1.5rem) from MASTER.md, with responsive variants
  const paddings = {
    none: '',
    sm: 'p-2 md:p-3 lg:p-4',      // 8px / 12px / 16px
    md: 'p-4 md:p-5 lg:p-6',      // 16px / 20px / 24px (design system default)
    lg: 'p-6 md:p-8 lg:p-10'      // 24px / 32px / 40px
  }
  return paddings[props.padding]
})
</script>
