import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2015',
    minify: 'esbuild', // Faster than terser, no extra dependency needed
    // If you want to drop console/debugger, use esbuild minify options
    // or switch back to terser after installing: npm install terser --save-dev
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'chart-vendor': ['chart.js', 'vue-chartjs'],
          'ui-vendor': ['@headlessui/vue', '@heroicons/vue'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: false,
    cssCodeSplit: true,
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios'],
  },
})
