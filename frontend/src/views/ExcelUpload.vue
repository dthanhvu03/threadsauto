<template>
  <div>
    <div class="mb-4 md:mb-6">
      <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1">📤 Excel Upload</h1>
      <p class="text-xs md:text-sm text-gray-600">Upload Excel file to create multiple jobs</p>
    </div>

    <Card class="mb-4 md:mb-6" padding="sm">
      <div class="space-y-4 md:space-y-6">
        <div>
          <label class="block text-xs md:text-sm font-semibold text-gray-700 mb-2 md:mb-3">
            Select Excel File
          </label>
          <div>
            <input
              type="file"
              accept=".xlsx,.xls"
              @change="handleFileSelect"
              class="block w-full text-sm text-gray-500 file:mr-4 file:py-2.5 md:file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs md:file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-700 file:cursor-pointer min-h-[44px] md:min-h-0"
            />
          </div>
        </div>
        <div v-if="selectedFile">
          <p class="text-xs md:text-sm text-gray-600 break-words">Selected: {{ selectedFile.name }}</p>
        </div>
        <div>
          <FormInput
            v-model="accountId"
            label="Account ID (Optional)"
            placeholder="Leave empty for all accounts"
          />
        </div>
        <div class="flex flex-col md:flex-row gap-2 md:space-x-3">
          <Button @click="handleUpload" :loading="uploading" :disabled="!selectedFile" class="w-full md:w-auto">
            Upload & Process
          </Button>
          <Button variant="outline" @click="downloadTemplate" class="w-full md:w-auto">Download Template</Button>
        </div>
      </div>
    </Card>

    <Alert
      v-if="uploadError"
      type="error"
      :message="uploadError"
      dismissible
      @dismiss="clearError"
    />

    <div v-if="uploadSuccess" class="mb-4 md:mb-6">
      <Alert
        type="success"
        :message="uploadSuccess"
        dismissible
        @dismiss="uploadSuccess = null"
      />
      <div v-if="jobsCreated > 0" class="mt-3">
        <Button
          @click="goToJobs"
          class="w-full md:w-auto"
        >
          📅 View Jobs ({{ jobsCreated }} created)
        </Button>
      </div>
    </div>

    <Card v-if="uploadResult">
      <template #header>
        <h3 class="text-base md:text-lg font-semibold">Upload Results</h3>
      </template>
      <div class="space-y-2">
        <p class="text-xs md:text-sm text-gray-600">Processing completed</p>
        <pre class="bg-gray-50 p-3 md:p-4 rounded-lg text-xs md:text-sm overflow-auto max-h-[400px]">{{ JSON.stringify(uploadResult, null, 2) }}</pre>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useExcel } from '@/features/excel/composables/useExcel'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import FormInput from '@/components/common/FormInput.vue'

const {
  loading: uploading,
  error: uploadError,
  uploadResult,
  uploadFile,
  downloadTemplate: downloadTemplateFile,
  clearError
} = useExcel()

const router = useRouter()
const selectedFile = ref(null)
const accountId = ref('')
const uploadSuccess = ref(null)
const jobsCreated = ref(0)

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    uploadError.value = 'Please select a file'
    return
  }

  uploadSuccess.value = null
  clearError()

  try {
    const result = await uploadFile(selectedFile.value, accountId.value || null)
    if (result && result.data) {
      const data = result.data
      jobsCreated.value = data.jobs_created || 0
      if (jobsCreated.value > 0) {
        uploadSuccess.value = `File uploaded successfully! Created ${jobsCreated.value} job(s). Jobs and Scheduler pages will be updated automatically.`
      } else {
        uploadSuccess.value = 'File uploaded successfully, but no scheduled posts found to create jobs.'
      }
      selectedFile.value = null
      
      // Note: WebSocket event will automatically trigger refresh in Jobs and Scheduler pages
      // No need to manually trigger refresh here
    }
  } catch (error) {
    // Error already set by composable
  }
}

const downloadTemplate = async () => {
  try {
    await downloadTemplateFile()
  } catch (error) {
    // Error already set by composable
  }
}

const goToJobs = async () => {
  // Navigate to Jobs page with account filter if accountId was provided
  // Don't filter by status - show all jobs for the account so newly created jobs are visible
  // Add reload=true to query to force refresh when Jobs page mounts
  if (accountId.value) {
    router.push({
      path: '/jobs',
      query: { 
        account_id: accountId.value,
        reload: 'true'  // Signal Jobs page to reload from server
      }
    })
  } else {
    router.push({
      path: '/jobs',
      query: { reload: 'true' }  // Signal Jobs page to reload from server
    })
  }
}
</script>
