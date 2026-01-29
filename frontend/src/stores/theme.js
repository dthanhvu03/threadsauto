import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: 'light' // 'light' or 'dark'
  }),

  getters: {
    isDark: (state) => state.mode === 'dark',
    isLight: (state) => state.mode === 'light'
  },

  actions: {
    setTheme(mode) {
      this.mode = mode
      // Apply theme to document
      if (mode === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      // Save to localStorage
      localStorage.setItem('theme', mode)
    },

    toggleTheme() {
      this.setTheme(this.mode === 'light' ? 'dark' : 'light')
    },

    initTheme() {
      // Load from localStorage or use system preference
      const saved = localStorage.getItem('theme')
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      const initialMode = saved || (prefersDark ? 'dark' : 'light')
      this.setTheme(initialMode)
    }
  }
})
