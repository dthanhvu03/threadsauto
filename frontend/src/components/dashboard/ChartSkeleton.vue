<template>
  <div 
    class="chart-skeleton" 
    :style="{ height: height }"
    role="status"
    aria-live="polite"
    aria-label="Loading chart data"
  >
    <div class="skeleton-content">
      <!-- Chart area skeleton -->
      <div class="skeleton-chart">
        <!-- Grid lines -->
        <div class="skeleton-grid">
          <div 
            v-for="i in 5" 
            :key="`grid-${i}`" 
            class="skeleton-grid-line"
            :style="{ top: `${(i - 1) * 20}%` }"
          />
        </div>
        
        <!-- Animated bars/lines -->
        <div class="skeleton-bars">
          <div 
            v-for="i in 8" 
            :key="`bar-${i}`" 
            class="skeleton-bar"
            :style="{ 
              left: `${(i - 1) * 12}%`,
              height: `${30 + Math.random() * 50}%`,
              animationDelay: `${i * 0.1}s`
            }"
          />
        </div>
      </div>
      
      <!-- Legend skeleton -->
      <div class="skeleton-legend">
        <div 
          v-for="i in 3" 
          :key="`legend-${i}`" 
          class="skeleton-legend-item"
        >
          <div class="skeleton-legend-color" />
          <div class="skeleton-legend-text" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  height: {
    type: String,
    default: '300px'
  }
})
</script>

<style scoped>
.chart-skeleton {
  position: relative;
  width: 100%;
  background: #ffffff;
  border-radius: 0.5rem;
  overflow: hidden;
}

.skeleton-content {
  padding: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.skeleton-chart {
  position: relative;
  flex: 1;
  min-height: 200px;
  background: linear-gradient(
    to bottom,
    rgba(249, 250, 251, 0.5) 0%,
    rgba(255, 255, 255, 0.5) 100%
  );
  border-radius: 0.375rem;
  overflow: hidden;
}

.skeleton-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.skeleton-grid-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent 0%,
    rgba(229, 231, 235, 0.5) 20%,
    rgba(229, 231, 235, 0.5) 80%,
    transparent 100%
  );
}

.skeleton-bars {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  padding: 0.5rem;
}

.skeleton-bar {
  position: absolute;
  bottom: 0;
  width: 8%;
  background: linear-gradient(
    to top,
    #e5e7eb 0%,
    #d1d5db 50%,
    #e5e7eb 100%
  );
  border-radius: 0.25rem 0.25rem 0 0;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% {
    opacity: 0.6;
    transform: scaleY(1);
  }
  50% {
    opacity: 1;
    transform: scaleY(1.05);
  }
}

.skeleton-legend {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  align-items: center;
  padding: 0.5rem 0;
}

.skeleton-legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.skeleton-legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #d1d5db;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-legend-text {
  width: 60px;
  height: 12px;
  background: linear-gradient(
    to right,
    #e5e7eb 0%,
    #d1d5db 50%,
    #e5e7eb 100%
  );
  border-radius: 0.25rem;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-bar,
  .skeleton-legend-color,
  .skeleton-legend-text {
    animation: none;
    opacity: 0.6;
  }
}
</style>
