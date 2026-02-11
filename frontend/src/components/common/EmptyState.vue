<template>
  <div class="text-center py-12">
    <div v-if="icon || iconName" class="mx-auto w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
      <component
        v-if="iconComponent"
        :is="iconComponent"
        class="h-8 w-8 text-gray-400"
      />
      <component
        v-else-if="icon"
        :is="icon"
        class="h-8 w-8 text-gray-400"
      />
    </div>
    <h3 v-if="title" class="mt-2 text-lg font-semibold text-gray-900">{{ title }}</h3>
    <p v-if="description" class="mt-1 text-sm text-gray-500 max-w-md mx-auto">{{ description }}</p>
    <div v-if="$slots.default || $slots.actions" class="mt-6">
      <slot />
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import * as HeroIcons from '@heroicons/vue/24/outline'

const props = defineProps({
  title: {
    type: String,
    default: null
  },
  description: {
    type: String,
    default: null
  },
  icon: {
    type: [Object, Function],
    default: null
  },
  iconName: {
    type: String,
    default: null
  }
})

const iconComponent = computed(() => {
  if (!props.iconName) return null
  const IconComponent = HeroIcons[props.iconName]
  return IconComponent || null
})
</script>
