<template>
  <div>
    <div class="mb-4 md:mb-6">
      <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1 flex items-center gap-2">
        <Cog6ToothIcon class="w-6 h-6 md:w-7 md:h-7" aria-hidden="true" />
        Configuration
      </h1>
      <p class="text-xs md:text-sm text-gray-600">Manage application settings</p>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <Alert
      v-if="saveSuccess"
      type="success"
      message="Configuration saved successfully"
      dismissible
      @dismiss="clearSuccess"
    />

    <Card v-if="!loading">
      <!-- Tabs Navigation -->
      <div class="border-b border-gray-200">
        <nav 
          class="-mb-px flex space-x-4 md:space-x-8 px-4 md:px-6 overflow-x-auto scrollbar-hide" 
          role="tablist"
          aria-label="Configuration tabs"
          style="scrollbar-width: none; -ms-overflow-style: none;"
        >
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'whitespace-nowrap py-3 md:py-4 px-2 md:px-1 border-b-2 font-medium text-sm transition-colors flex-shrink-0 min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
            :role="'tab'"
            :aria-selected="activeTab === tab.id"
            :aria-controls="`tab-panel-${tab.id}`"
            :id="`tab-${tab.id}`"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <form @submit.prevent="handleSave" class="p-4 md:p-6" aria-label="Configuration form">
        <!-- General Tab -->
        <div 
          v-show="activeTab === 'general'" 
          :id="'tab-panel-general'"
          role="tabpanel"
          :aria-labelledby="'tab-general'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <FormSelect
              v-model="config.run_mode"
              label="Run Mode"
              hint="Controls automation speed and safety"
              :options="[
                { value: 'SAFE', label: 'Safe Mode' },
                { value: 'FAST', label: 'Fast Mode' }
              ]"
            />
          </div>

          <div>
            <FormSelect
              v-model="config.selectors.version"
              label="Selector Version"
              :options="[
                { value: 'v1', label: 'Version 1' },
                { value: 'v2', label: 'Version 2' }
              ]"
            />
          </div>

          <div>
            <FormSelect
              v-model="config.selectors.platform"
              label="Platform"
              :options="[
                { value: 'threads', label: 'Threads' },
                { value: 'facebook', label: 'Facebook' }
              ]"
            />
          </div>

          <FormCheckbox
            v-model="config.selectors.use_custom"
            label="Use Custom Selectors"
          />
        </div>

        <!-- Browser Tab -->
        <div 
          v-show="activeTab === 'browser'" 
          :id="'tab-panel-browser'"
          role="tabpanel"
          :aria-labelledby="'tab-browser'"
          class="space-y-4 md:space-y-6"
        >
          <FormCheckbox
            v-model="config.browser.headless"
            label="Headless Mode"
          />

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Slow Motion (ms)
            </label>
            <FormInput
              v-model="config.browser.slow_mo"
              type="number"
              placeholder="100"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Default Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.timeout"
              type="number"
              placeholder="30000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Navigation Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.navigation_timeout"
              type="number"
              placeholder="30000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Element Wait Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.element_wait_timeout"
              type="number"
              placeholder="10000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Short Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.short_timeout"
              type="number"
              placeholder="5000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Very Short Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.very_short_timeout"
              type="number"
              placeholder="3000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Long Wait Timeout (ms)
            </label>
            <FormInput
              v-model="config.browser.long_wait_timeout"
              type="number"
              placeholder="15000"
            />
          </div>

          <FormCheckbox
            v-model="config.browser.debug"
            label="Debug Mode"
          />
        </div>

        <!-- Anti-Detection Tab -->
        <div 
          v-show="activeTab === 'anti_detection'" 
          :id="'tab-panel-anti_detection'"
          role="tabpanel"
          :aria-labelledby="'tab-anti_detection'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Min Delay (seconds)
            </label>
            <FormInput
              v-model="config.anti_detection.min_delay"
              type="number"
              step="0.1"
              placeholder="0.5"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Max Delay (seconds)
            </label>
            <FormInput
              v-model="config.anti_detection.max_delay"
              type="number"
              step="0.1"
              placeholder="2.0"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Typing Chunk Size
            </label>
            <FormInput
              v-model="config.anti_detection.typing_chunk_size"
              type="number"
              placeholder="4"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Typing Delay Min (seconds)
            </label>
            <FormInput
              v-model="config.anti_detection.typing_delay_min"
              type="number"
              step="0.01"
              placeholder="0.05"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Typing Delay Max (seconds)
            </label>
            <FormInput
              v-model="config.anti_detection.typing_delay_max"
              type="number"
              step="0.01"
              placeholder="0.15"
            />
          </div>
        </div>

        <!-- Safety Tab -->
        <div 
          v-show="activeTab === 'safety'" 
          :id="'tab-panel-safety'"
          role="tabpanel"
          :aria-labelledby="'tab-safety'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Max Posts Per Day
            </label>
            <FormInput
              v-model="config.safety.max_posts_per_day"
              type="number"
              placeholder="10"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Min Delay Between Posts (seconds)
            </label>
            <FormInput
              v-model="config.safety.min_delay_between_posts"
              type="number"
              placeholder="5"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Rate Limit Window (seconds)
            </label>
            <FormInput
              v-model="config.safety.rate_limit_window"
              type="number"
              placeholder="60"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Rate Limit Max Actions
            </label>
            <FormInput
              v-model="config.safety.rate_limit_max_actions"
              type="number"
              placeholder="10"
            />
          </div>

          <FormCheckbox
            v-model="config.safety.auto_pause_on_high_risk"
            label="Auto Pause on High Risk"
          />

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              High Risk Threshold
            </label>
            <FormInput
              v-model="config.safety.high_risk_threshold"
              type="number"
              placeholder="3"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Consecutive Error Threshold
            </label>
            <FormInput
              v-model="config.safety.consecutive_error_threshold"
              type="number"
              placeholder="5"
            />
          </div>
        </div>

        <!-- Scheduler Tab -->
        <div 
          v-show="activeTab === 'scheduler'" 
          :id="'tab-panel-scheduler'"
          role="tabpanel"
          :aria-labelledby="'tab-scheduler'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Max Retries
            </label>
            <FormInput
              v-model="config.scheduler.max_retries"
              type="number"
              placeholder="3"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Max Running Minutes
            </label>
            <FormInput
              v-model="config.scheduler.max_running_minutes"
              type="number"
              placeholder="30"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Check Interval (seconds)
            </label>
            <FormInput
              v-model="config.scheduler.check_interval_seconds"
              type="number"
              placeholder="10"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Reload Interval (seconds)
            </label>
            <FormInput
              v-model="config.scheduler.reload_interval_seconds"
              type="number"
              placeholder="30"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Reload Check Delay (seconds)
            </label>
            <FormInput
              v-model="config.scheduler.reload_check_delay_seconds"
              type="number"
              placeholder="2"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Processing Delay (seconds)
            </label>
            <FormInput
              v-model="config.scheduler.processing_delay_seconds"
              type="number"
              step="0.1"
              placeholder="4.0"
            />
          </div>
        </div>

        <!-- Platform URLs Tab -->
        <div 
          v-show="activeTab === 'platform'" 
          :id="'tab-panel-platform'"
          role="tabpanel"
          :aria-labelledby="'tab-platform'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Base URL
            </label>
            <FormInput
              v-model="config.platform.threads_base_url"
              type="url"
              placeholder="https://www.threads.com/?hl=vi"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Compose URL
            </label>
            <FormInput
              v-model="config.platform.threads_compose_url"
              type="url"
              placeholder="https://www.threads.com/?hl=vi/compose"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Login URL
            </label>
            <FormInput
              v-model="config.platform.threads_login_url"
              type="url"
              placeholder="https://threads.net/login"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Profile URL
            </label>
            <FormInput
              v-model="config.platform.threads_profile_url"
              type="url"
              placeholder="https://www.threads.com/"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Post URL Template
            </label>
            <FormInput
              v-model="config.platform.threads_post_url_template"
              type="url"
              placeholder="https://www.threads.com/@{username}/post/{thread_id}"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Threads Post Fallback Template
            </label>
            <FormInput
              v-model="config.platform.threads_post_fallback_template"
              type="url"
              placeholder="https://www.threads.com/post/{thread_id}"
              autocomplete="url"
              spellcheck="false"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Facebook URL
            </label>
            <FormInput
              v-model="config.platform.facebook_url"
              type="url"
              placeholder="https://www.facebook.com"
              autocomplete="url"
              spellcheck="false"
            />
          </div>
        </div>

        <!-- Analytics Tab -->
        <div 
          v-show="activeTab === 'analytics'" 
          :id="'tab-panel-analytics'"
          role="tabpanel"
          :aria-labelledby="'tab-analytics'"
          class="space-y-4 md:space-y-6"
        >
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Fetch Metrics Timeout (seconds)
            </label>
            <FormInput
              v-model="config.analytics.fetch_metrics_timeout_seconds"
              type="number"
              placeholder="30"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Page Load Delay (seconds)
            </label>
            <FormInput
              v-model="config.analytics.page_load_delay_seconds"
              type="number"
              step="0.1"
              placeholder="2.0"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Page Load Alt Delay (seconds)
            </label>
            <FormInput
              v-model="config.analytics.page_load_alt_delay_seconds"
              type="number"
              step="0.1"
              placeholder="3.0"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Username Extraction Timeout (seconds)
            </label>
            <FormInput
              v-model="config.analytics.username_extraction_timeout_seconds"
              type="number"
              placeholder="30"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Username Page Load Delay (seconds)
            </label>
            <FormInput
              v-model="config.analytics.username_page_load_delay_seconds"
              type="number"
              step="0.1"
              placeholder="3.0"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Username Element Wait Timeout (ms)
            </label>
            <FormInput
              v-model="config.analytics.username_element_wait_timeout_ms"
              type="number"
              placeholder="5000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Username Click Timeout (ms)
            </label>
            <FormInput
              v-model="config.analytics.username_click_timeout_ms"
              type="number"
              placeholder="10000"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Username Navigation Delay (seconds)
            </label>
            <FormInput
              v-model="config.analytics.username_navigation_delay_seconds"
              type="number"
              step="0.1"
              placeholder="2.0"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Delay Between Fetches (seconds)
            </label>
            <FormInput
              v-model="config.analytics.delay_between_fetches_seconds"
              type="number"
              step="0.1"
              placeholder="2.0"
            />
          </div>

          <FormCheckbox
            v-model="config.analytics.parallel_fetch_enabled"
            label="Parallel Fetch Enabled"
          />

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Max Concurrent Fetches
            </label>
            <FormInput
              v-model="config.analytics.max_concurrent_fetches"
              type="number"
              placeholder="3"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1 md:mb-2">
              Recent Metrics Hours
            </label>
            <FormInput
              v-model="config.analytics.recent_metrics_hours"
              type="number"
              placeholder="1"
            />
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col md:flex-row justify-end space-y-2 md:space-y-0 md:space-x-3 pt-4 md:pt-6 border-t border-gray-200 mt-4 md:mt-6">
          <Button 
            variant="outline" 
            type="button" 
            @click="handleReset" 
            class="w-full md:w-auto"
            :disabled="loading"
            aria-label="Reset configuration to saved values"
          >
            <ArrowPathIcon class="w-4 h-4 mr-1.5" aria-hidden="true" />
            Reset
          </Button>
          <Button 
            type="submit" 
            :loading="loading" 
            :disabled="loading"
            class="w-full md:w-auto"
            aria-label="Save configuration changes"
          >
            <CheckIcon v-if="!loading" class="w-4 h-4 mr-1.5" aria-hidden="true" />
            Save Changes
          </Button>
        </div>
      </form>
    </Card>

    <div v-if="loading" class="flex justify-center py-12" role="status" aria-live="polite">
      <LoadingSpinner size="lg" />
      <span class="sr-only">Loading configuration...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch } from 'vue'
import { useConfig } from '@/features/config/composables/useConfig'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import FormInput from '@/components/common/FormInput.vue'
import FormSelect from '@/components/common/FormSelect.vue'
import FormCheckbox from '@/components/common/FormCheckbox.vue'
import { 
  Cog6ToothIcon, 
  ArrowPathIcon, 
  CheckIcon 
} from '@heroicons/vue/24/outline'

const {
  config: storeConfig,
  loading,
  error,
  saveSuccess,
  fetchConfig,
  updateConfig,
  clearError,
  clearSuccess
} = useConfig()

const activeTab = ref('general')

const tabs = [
  { id: 'general', label: 'General' },
  { id: 'browser', label: 'Browser' },
  { id: 'anti_detection', label: 'Anti-Detection' },
  { id: 'safety', label: 'Safety' },
  { id: 'scheduler', label: 'Scheduler' },
  { id: 'platform', label: 'Platform URLs' },
  { id: 'analytics', label: 'Analytics' }
]

// Initialize config with defaults
const config = reactive({
  run_mode: 'SAFE',
  selectors: {
    version: 'v1',
    use_custom: false,
    platform: 'threads'
  },
  browser: {
    headless: false,
    slow_mo: 100,
    timeout: 30000,
    debug: false,
    navigation_timeout: 30000,
    element_wait_timeout: 10000,
    short_timeout: 5000,
    very_short_timeout: 3000,
    long_wait_timeout: 15000
  },
  anti_detection: {
    min_delay: 0.5,
    max_delay: 2.0,
    typing_chunk_size: 4,
    typing_delay_min: 0.05,
    typing_delay_max: 0.15
  },
  safety: {
    max_posts_per_day: 10,
    min_delay_between_posts: 5,
    rate_limit_window: 60,
    rate_limit_max_actions: 10,
    auto_pause_on_high_risk: true,
    high_risk_threshold: 3,
    consecutive_error_threshold: 5
  },
  scheduler: {
    max_retries: 3,
    max_running_minutes: 30,
    check_interval_seconds: 10,
    reload_interval_seconds: 30,
    reload_check_delay_seconds: 2,
    processing_delay_seconds: 4.0
  },
  platform: {
    threads_base_url: 'https://www.threads.com/?hl=vi',
    threads_compose_url: 'https://www.threads.com/?hl=vi/compose',
    threads_login_url: 'https://threads.net/login',
    threads_profile_url: 'https://www.threads.com/',
    threads_post_url_template: 'https://www.threads.com/@{username}/post/{thread_id}',
    threads_post_fallback_template: 'https://www.threads.com/post/{thread_id}',
    facebook_url: 'https://www.facebook.com'
  },
  analytics: {
    fetch_metrics_timeout_seconds: 30,
    page_load_delay_seconds: 2.0,
    page_load_alt_delay_seconds: 3.0,
    username_extraction_timeout_seconds: 30,
    username_page_load_delay_seconds: 3.0,
    username_element_wait_timeout_ms: 5000,
    username_click_timeout_ms: 10000,
    username_navigation_delay_seconds: 2.0,
    delay_between_fetches_seconds: 2.0,
    parallel_fetch_enabled: true,
    max_concurrent_fetches: 3,
    recent_metrics_hours: 1
  }
})

// Load config data into reactive object
const loadConfigToForm = (data) => {
  if (!data) return
  
  // Update top-level
  if (data.run_mode) config.run_mode = data.run_mode
  if (data.mode) config.run_mode = data.mode
  
  // Update nested objects
  if (data.selectors) Object.assign(config.selectors, data.selectors)
  if (data.browser) Object.assign(config.browser, data.browser)
  if (data.anti_detection) Object.assign(config.anti_detection, data.anti_detection)
  if (data.safety) Object.assign(config.safety, data.safety)
  if (data.scheduler) Object.assign(config.scheduler, data.scheduler)
  if (data.platform) Object.assign(config.platform, data.platform)
  if (data.analytics) Object.assign(config.analytics, data.analytics)
}

const handleSave = async () => {
  // Convert reactive object to plain object for API
  const configData = {
    run_mode: config.run_mode,
    selectors: { ...config.selectors },
    browser: { ...config.browser },
    anti_detection: { ...config.anti_detection },
    safety: { ...config.safety },
    scheduler: { ...config.scheduler },
    platform: { ...config.platform },
    analytics: { ...config.analytics }
  }
  
  await updateConfig(configData)
  // Reload config after save to sync with server
  const updatedConfig = await fetchConfig()
  if (updatedConfig) {
    loadConfigToForm(updatedConfig)
  }
}

const handleReset = async () => {
  // Confirmation dialog for reset action (UX guidelines)
  const confirmed = window.confirm(
    'Are you sure you want to reset all changes? This will discard any unsaved modifications and reload the saved configuration.'
  )
  if (confirmed) {
    const configData = await fetchConfig()
    if (configData) {
      loadConfigToForm(configData)
    }
  }
}

// Watch for config changes from store
watch(storeConfig, (newConfig) => {
  if (newConfig) {
    loadConfigToForm(newConfig)
  }
}, { immediate: true })

onMounted(async () => {
  const configData = await fetchConfig()
  if (configData) {
    loadConfigToForm(configData)
  }
})
</script>

<style scoped>
/* Hide scrollbar for tabs navigation */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
