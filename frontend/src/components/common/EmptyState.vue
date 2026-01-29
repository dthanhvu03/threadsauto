<template>
  <div class="text-center py-12">
    <div v-if="icon" class="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
      <component
        :is="icon"
        class="h-6 w-6 text-gray-400"
      />
    </div>
    <h3 v-if="title" class="mt-2 text-sm font-medium text-gray-900">{{ title }}</h3>
    <p v-if="description" class="mt-1 text-sm text-gray-500">{{ description }}</p>
    <div v-if="$slots.default || $slots.actions" class="mt-6">
      <slot />
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
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
  }
})
</script>
