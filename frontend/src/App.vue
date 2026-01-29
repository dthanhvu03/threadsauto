<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <RouterView />
    <SpeedInsights />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { SpeedInsights } from '@vercel/speed-insights/vue'
</script>
