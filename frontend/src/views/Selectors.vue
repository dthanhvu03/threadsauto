<template>
  <div>
    <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 md:gap-0">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1">🎯 Selectors</h1>
        <p class="text-xs md:text-sm text-gray-600">Manage CSS selectors for UI elements</p>
      </div>
      <div class="flex flex-col md:flex-row gap-2 md:space-x-3 w-full md:w-auto">
        <select
          v-model="selectedPlatform"
          @change="handlePlatformChange"
          class="block w-full md:w-auto rounded-md border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm bg-white px-3 py-2.5 md:py-2 min-h-[44px] md:min-h-[38px]"
        >
          <option value="threads">Threads</option>
          <option value="facebook">Facebook</option>
        </select>
        <select
          v-model="selectedVersion"
          @change="handleVersionChange"
          class="block w-full md:w-auto rounded-md border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm bg-white px-3 py-2.5 md:py-2 min-h-[44px] md:min-h-[38px]"
        >
          <option value="v1">Version 1</option>
          <option value="v2">Version 2</option>
        </select>
        <Button @click="handleSave" :loading="loading" class="w-full md:w-auto">
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
      v-if="saveSuccess"
      type="success"
      message="Selectors saved successfully"
      dismissible
      @dismiss="clearSuccess"
    />

    <div v-if="loading" class="flex justify-center py-12">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else-if="selectorGroups.length === 0" class="py-8">
      <EmptyState
        title="No selectors"
        description="No selectors found for this platform and version"
      />
    </div>

    <div v-else class="space-y-4">
      <!-- Selector Groups -->
      <Card v-for="group in selectorGroups" :key="group.name" class="mb-4">
        <template #header>
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-2 md:gap-0">
            <h3 class="text-base md:text-lg font-semibold text-gray-900">
              {{ formatSelectorName(group.name) }}
            </h3>
            <Button
              variant="outline"
              size="sm"
              @click="addSelector(group.name)"
              class="w-full md:w-auto"
            >
              + Add Selector
            </Button>
          </div>
        </template>

        <div class="space-y-3">
          <div
            v-for="(selector, index) in group.selectors"
            :key="`${group.name}-${index}`"
            class="flex items-start space-x-2"
          >
            <div class="flex-1">
              <FormInput
                :model-value="selector"
                @update:model-value="updateSelector(group.name, index, $event)"
                :placeholder="`Enter selector for ${formatSelectorName(group.name)}`"
                class="font-mono text-sm"
              />
            </div>
            <button
              type="button"
              @click="removeSelector(group.name, index)"
              class="inline-flex items-center justify-center p-2.5 md:p-2 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0"
              title="Remove selector"
            >
              <TrashIcon class="h-5 w-5 md:h-4 md:w-4" />
            </button>
          </div>

          <p v-if="group.selectors.length === 0" class="text-sm text-gray-500 italic">
            No selectors. Click "+ Add Selector" to add one.
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
import { TrashIcon } from '@heroicons/vue/24/outline'

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
const handlePlatformChange = async () => {
  try {
    await setPlatform(selectedPlatform.value)
    loadSelectorsToForm()
  } catch (error) {
    console.error('Error changing platform:', error)
  }
}

// Handle version change
const handleVersionChange = async () => {
  await setVersion(selectedVersion.value)
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
      alert('Please add at least one selector')
      return
    }
    
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
  } catch (error) {
    console.error('Error saving selectors:', error)
    alert('Failed to save selectors: ' + (error.message || 'Unknown error'))
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
