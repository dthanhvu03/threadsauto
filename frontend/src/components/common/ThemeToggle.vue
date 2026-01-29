<template>
  <button
    @click="toggleTheme"
    class="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 transition-colors"
    :title="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    aria-label="Toggle theme"
  >
    <SunIcon v-if="themeStore.isDark" class="h-5 w-5" />
    <MoonIcon v-else class="h-5 w-5" />
  </button>
</template>

<script setup>
import { onMounted } from 'vue'
import { SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

const toggleTheme = () => {
  themeStore.toggleTheme()
}

onMounted(() => {
  themeStore.initTheme()
})
</script>
