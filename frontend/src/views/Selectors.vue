<template>
  <div>
    <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 md:gap-0">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <CursorArrowRaysIcon class="w-6 h-6 md:w-7 md:h-7" aria-hidden="true" />
          Selectors
        </h1>
        <p class="text-xs md:text-sm text-gray-600">Manage CSS selectors for UI elements</p>
      </div>
      <div class="flex flex-col md:flex-row gap-2 md:space-x-3 w-full md:w-auto" role="toolbar" aria-label="Selector filters and actions">
        <FormSelect
          v-model="selectedPlatform"
          @update:model-value="handlePlatformChange"
          label="Platform"
          :options="[
            { value: 'threads', label: 'Threads' },
            { value: 'facebook', label: 'Facebook' }
          ]"
          class="w-full md:w-auto"
          :hide-label-on-mobile="true"
        />
        <FormSelect
          v-model="selectedVersion"
          @update:model-value="handleVersionChange"
          label="Version"
          :options="[
            { value: 'v1', label: 'Version 1' },
            { value: 'v2', label: 'Version 2' }
          ]"
          class="w-full md:w-auto"
          :hide-label-on-mobile="true"
        />
        <Button 
          @click="handleSave" 
          :loading="loading" 
          :disabled="loading"
          class="w-full md:w-auto"
          aria-label="Save all selector changes"
        >
          <CheckIcon v-if="!loading" class="w-4 h-4 mr-1.5" aria-hidden="true" />
          Save Selectors
        </Button>
      </div>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <Alert
      v-if="validationError"
      type="error"
      :message="validationError"
      dismissible
      @dismiss="validationError = null"
    />

    <Alert
      v-if="saveSuccess"
      type="success"
      message="Selectors saved successfully"
      dismissible
      @dismiss="clearSuccess"
    />

    <div v-if="loading" class="flex justify-center py-12" role="status" aria-live="polite">
      <LoadingSpinner size="lg" />
      <span class="sr-only">Loading selectors...</span>
    </div>

    <div v-else-if="selectorGroups.length === 0" class="py-8">
      <EmptyState
        title="No selectors"
        description="No selectors found for this platform and version"
      />
    </div>

    <div v-else class="space-y-4" role="region" aria-label="Selector groups">
      <!-- Selector Groups -->
      <Card 
        v-for="group in selectorGroups" 
        :key="group.name" 
        class="mb-4" 
        role="article" 
        :aria-labelledby="`selector-group-${group.name}`"
      >
        <template #header>
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-2 md:gap-0">
            <h3 :id="`selector-group-${group.name}`" class="text-base md:text-lg font-semibold text-gray-900">
              {{ formatSelectorName(group.name) }}
            </h3>
            <Button
              variant="outline"
              size="sm"
              @click="addSelector(group.name)"
              class="w-full md:w-auto"
              :aria-label="`Add new selector for ${formatSelectorName(group.name)}`"
            >
              <PlusIcon class="w-4 h-4 mr-1" aria-hidden="true" />
              Add Selector
            </Button>
          </div>
        </template>

        <div class="space-y-3" role="list" :aria-label="`Selectors for ${formatSelectorName(group.name)}`">
          <div
            v-for="(selector, index) in group.selectors"
            :key="`${group.name}-${index}`"
            class="flex items-start space-x-2"
            role="listitem"
          >
            <div class="flex-1">
              <FormInput
                :model-value="selector"
                @update:model-value="updateSelector(group.name, index, $event)"
                :placeholder="`Enter selector for ${formatSelectorName(group.name)}`"
                :label="`Selector ${index + 1}`"
                :id="`selector-${group.name}-${index}`"
                class="font-mono text-sm"
                autocomplete="off"
                spellcheck="false"
                :aria-label="`CSS selector ${index + 1} for ${formatSelectorName(group.name)}`"
              />
            </div>
            <button
              type="button"
              @click="removeSelector(group.name, index)"
              class="inline-flex items-center justify-center p-2.5 md:p-2 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 transition-colors"
              :aria-label="`Remove selector ${index + 1} for ${formatSelectorName(group.name)}`"
              title="Remove selector"
            >
              <TrashIcon class="h-5 w-5 md:h-4 md:w-4" aria-hidden="true" />
              <span class="sr-only">Remove</span>
            </button>
          </div>

          <p v-if="group.selectors.length === 0" class="text-sm text-gray-500 italic" role="status">
            No selectors. Click "Add Selector" to add one.
          </p>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSelectors } from '@/features/selectors/composables/useSelectors'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FormInput from '@/components/common/FormInput.vue'
import FormSelect from '@/components/common/FormSelect.vue'
import { 
  CursorArrowRaysIcon, 
  TrashIcon, 
  PlusIcon, 
  CheckIcon 
} from '@heroicons/vue/24/outline'

const {
  selectors: storeSelectors,
  currentVersion,
  currentPlatform,
  loading,
  error,
  saveSuccess,
  fetchSelectors,
  updateSelectors,
  setVersion,
  setPlatform,
  clearError,
  clearSuccess
} = useSelectors()

const selectedPlatform = ref('threads')
const selectedVersion = ref('v1')

// Local state cho form data
const formData = ref({})

// Local validation error (separate from composable error)
const validationError = ref(null)

// Computed: Convert formData thành selectorGroups cho display
const selectorGroups = computed(() => {
  return Object.keys(formData.value)
    .sort()
    .map(selectorName => ({
      name: selectorName,
      selectors: formData.value[selectorName] || []
    }))
    .filter(group => group.selectors.length > 0 || true) // Show all groups
})

// Format selector name để hiển thị (convert snake_case to Title Case)
const formatSelectorName = (name) => {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Update selector value
const updateSelector = (selectorName, index, value) => {
  if (!formData.value[selectorName]) {
    formData.value[selectorName] = []
  }
  formData.value[selectorName][index] = value
}

// Add new selector input
const addSelector = (selectorName) => {
  if (!formData.value[selectorName]) {
    formData.value[selectorName] = []
  }
  formData.value[selectorName].push('')
}

// Remove selector
const removeSelector = (selectorName, index) => {
  if (formData.value[selectorName]) {
    formData.value[selectorName].splice(index, 1)
    // Nếu không còn selector nào, giữ array rỗng
    if (formData.value[selectorName].length === 0) {
      // Option: có thể xóa key hoặc giữ rỗng
      // formData.value[selectorName] = []
    }
  }
}

// Load selectors vào form
const loadSelectorsToForm = () => {
  if (storeSelectors.value) {
    // Deep copy để có thể edit
    formData.value = {}
    Object.keys(storeSelectors.value).forEach(selectorName => {
      const selectors = storeSelectors.value[selectorName]
      formData.value[selectorName] = Array.isArray(selectors) 
        ? [...selectors] 
        : [selectors].filter(Boolean)
    })
  } else {
    formData.value = {}
  }
}

// Handle platform change
const handlePlatformChange = async (newPlatform) => {
  if (!newPlatform) return
  try {
    await setPlatform(newPlatform)
    loadSelectorsToForm()
  } catch (error) {
    console.error('Error changing platform:', error)
  }
}

// Handle version change
const handleVersionChange = async (newVersion) => {
  if (!newVersion) return
  await setVersion(newVersion)
  loadSelectorsToForm()
}

// Handle save
const handleSave = async () => {
  try {
    // Collect data từ form
    const selectorsToSave = {}
    
    Object.keys(formData.value).forEach(selectorName => {
      const selectors = formData.value[selectorName]
        .map(s => s.trim())
        .filter(s => s.length > 0) // Remove empty strings
      
      if (selectors.length > 0) {
        selectorsToSave[selectorName] = selectors
      }
    })
    
    if (Object.keys(selectorsToSave).length === 0) {
      // Use proper error handling instead of alert (UX guidelines)
      validationError.value = 'Please add at least one selector before saving'
      return
    }
    
    // Clear validation error if validation passes
    validationError.value = null
    
    const result = await updateSelectors({
      platform: selectedPlatform.value,
      version: selectedVersion.value,
      selectors: selectorsToSave
    })
    
    if (result) {
      // Reload để sync với server
      await fetchSelectors(selectedVersion.value, selectedPlatform.value)
      loadSelectorsToForm()
    }
  } catch (err) {
    console.error('Error saving selectors:', err)
    // Error will be handled by composable and displayed via Alert component
    // No need for alert() - better UX with inline error display
  }
}

// Watch for selectors changes
watch(storeSelectors, () => {
  loadSelectorsToForm()
}, { deep: true })

// Watch for platform/version changes
watch(currentPlatform, (newPlatform) => {
  if (newPlatform) {
    selectedPlatform.value = newPlatform
  }
})

watch(currentVersion, (newVersion) => {
  if (newVersion) {
    selectedVersion.value = newVersion
  }
})

onMounted(async () => {
  selectedPlatform.value = currentPlatform.value || 'threads'
  selectedVersion.value = currentVersion.value || 'v1'
  await fetchSelectors(selectedVersion.value, selectedPlatform.value)
  loadSelectorsToForm()
})
</script>

<style scoped>
.font-mono {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
}
</style>
