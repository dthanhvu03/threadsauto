# Jobs Feature Module

This module implements the jobs feature using the new architecture pattern with service layer, composables, and state management.

## Structure

```
jobs/
├── __init__.js          # Feature marker
├── index.js             # Central exports
├── README.md            # This file
├── types/
│   └── jobTypes.js      # JSDoc type definitions
├── services/
│   └── jobsService.js   # API service layer
├── composables/
│   └── useJobs.js      # Business logic composable
├── store/
│   └── jobsStore.js     # State management only
└── views/
    └── JobsView.vue     # Example view component
```

## Usage

### Using the Composable (Recommended)

```javascript
import { useJobs } from '@/features/jobs/composables/useJobs'

export default {
  setup() {
    const {
      jobs,
      loading,
      error,
      filteredJobs,
      fetchJobs,
      createJob,
      deleteJob,
      setFilters,
      clearFilters
    } = useJobs()

    // Fetch jobs on mount
    onMounted(async () => {
      await fetchJobs({ accountId: 'account_001' })
    })

    // Create job
    const handleCreate = async (jobData) => {
      await createJob(jobData)
    }

    return {
      jobs,
      loading,
      error,
      filteredJobs,
      handleCreate
    }
  }
}
```

### Using the Service Directly

```javascript
import { jobsService } from '@/features/jobs/services/jobsService'

// Get all jobs
const response = await jobsService.getAll({ account_id: 'account_001' })

// Create job
const newJob = await jobsService.create({
  account_id: 'account_001',
  content: 'Hello Threads!',
  scheduled_time: '2024-01-01T10:00:00Z',
  platform: 'THREADS',
  priority: 'NORMAL'
})
```

### Using the Store Directly

```javascript
import { useJobsStore } from '@/features/jobs/store/jobsStore'

const store = useJobsStore()

// Set jobs (usually done by composable)
store.setJobs(jobs)

// Access state
const jobs = store.jobs
const filters = store.filters

// Update filters
store.setFilters({ accountId: 'account_001' })
```

## API

### JobsService

All methods return a Promise that resolves to the API response object.

- `getAll(filters)` - Get all jobs
- `getById(jobId)` - Get job by ID
- `create(jobData)` - Create new job
- `update(jobId, jobData)` - Update job
- `delete(jobId)` - Delete job
- `getStats(accountId)` - Get statistics

### useJobs Composable

Returns reactive state and methods:

**State:**
- `jobs` - Array of jobs
- `selectedJob` - Currently selected job
- `filters` - Current filter values
- `loading` - Loading state
- `error` - Error message

**Computed:**
- `filteredJobs` - Jobs filtered by current filters
- `jobsByStatus` - Jobs grouped by status

**Methods:**
- `fetchJobs(options)` - Fetch jobs
- `fetchJobById(jobId)` - Fetch single job
- `createJob(jobData)` - Create job
- `updateJob(jobId, jobData)` - Update job
- `deleteJob(jobId)` - Delete job
- `fetchStats(accountId)` - Get statistics
- `setFilters(filters)` - Update filters
- `clearFilters()` - Reset filters
- `clearError()` - Clear error

### JobsStore

**State:**
- `jobs` - Array of jobs
- `selectedJob` - Selected job
- `error` - Error message
- `filters` - Filter values

**Getters:**
- `jobsByStatus` - Jobs grouped by status

**Actions:**
- `setJobs(jobs)` - Set jobs array
- `setSelectedJob(job)` - Set selected job
- `removeJob(jobId)` - Remove job
- `setError(error)` - Set error
- `setFilters(filters)` - Update filters
- `clearFilters()` - Reset filters
- `reset()` - Reset entire store

## Type Definitions

See `types/jobTypes.js` for JSDoc type definitions:
- `Job` - Job object structure
- `JobCreateData` - Job creation data
- `JobUpdateData` - Job update data
- `JobFilters` - Filter options
- `JobStats` - Statistics structure

## Migration from Old Store

The old store (`@/stores/jobs`) is still available for backward compatibility. To migrate:

1. Replace `useJobsStore` import with `useJobs` composable
2. Replace store actions with composable methods
3. Use composable state instead of store state
4. Remove direct API calls from components

Example migration:

```javascript
// Before
import { useJobsStore } from '@/stores/jobs'
const store = useJobsStore()
await store.fetchJobs()

// After
import { useJobs } from '@/features/jobs/composables/useJobs'
const { fetchJobs } = useJobs()
await fetchJobs()
```

## Testing

### Mock Service

```javascript
import { jobsService } from '@/features/jobs/services/jobsService'

jest.mock('@/features/jobs/services/jobsService', () => ({
  jobsService: {
    getAll: jest.fn(),
    create: jest.fn()
  }
}))
```

### Test Composable

```javascript
import { useJobs } from '@/features/jobs/composables/useJobs'
import { jobsService } from '@/features/jobs/services/jobsService'

test('fetchJobs updates state', async () => {
  jobsService.getAll.mockResolvedValue({
    success: true,
    data: [{ job_id: '1', content: 'Test' }]
  })

  const { fetchJobs, jobs } = useJobs()
  await fetchJobs()

  expect(jobs.value).toHaveLength(1)
})
```

## Best Practices

1. **Use composable in components** - Don't access store or service directly
2. **Service for API calls only** - No business logic in services
3. **Store for state only** - No API calls or business logic in stores
4. **Composable for business logic** - Orchestrate services and stores
5. **Type definitions** - Use JSDoc types for better IDE support
