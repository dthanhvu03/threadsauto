# API Contract Documentation

This document defines the contract between frontend and backend API.

## Response Format

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "meta": {
    "timestamp": "2026-01-25T10:00:00Z",
    "request_id": "req_123456"
  },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2026-01-25T10:00:00Z",
    "request_id": "req_123456"
  }
}
```

## Error Codes

- `VALIDATION_ERROR` (400) - Input validation failed
- `UNAUTHORIZED` (401) - Authentication required
- `FORBIDDEN` (403) - Permission denied
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Resource conflict
- `INTERNAL_ERROR` (500) - Server error
- `BAD_REQUEST` (400) - Bad request
- `HTTP_ERROR` - Generic HTTP error

## Endpoint Naming

All endpoints follow RESTful conventions:

- `GET /api/{resource}` - List resources
- `GET /api/{resource}/{id}` - Get resource by ID
- `POST /api/{resource}` - Create resource
- `PUT /api/{resource}/{id}` - Update resource
- `DELETE /api/{resource}/{id}` - Delete resource

## Query Parameters

- Filter: `?status=pending&account_id=123`
- Pagination: `?page=1&limit=20`
- Sort: `?sort=created_at&order=desc`
- Search: `?q=keyword`

## Frontend Usage

### Using BaseService

```javascript
import { BaseService } from '@/core/api/baseService'

class JobsService extends BaseService {
  constructor() {
    super('/jobs')
  }

  async getAll(filters = {}) {
    return this.get('', filters)
  }

  async getById(id) {
    return this.get(`/${id}`)
  }

  async create(data) {
    return this.post('', data)
  }
}

export const jobsService = new JobsService()
```

### Using useApi Composable

```javascript
import { useApi } from '@/core/composables/useApi'
import { jobsService } from '@/features/jobs/services/jobsService'

export function useJobs() {
  const { data, loading, error, execute } = useApi({
    apiCall: jobsService.getAll,
    initialData: []
  })

  const fetchJobs = async (filters = {}) => {
    return execute(filters)
  }

  return {
    jobs: data,
    loading,
    error,
    fetchJobs
  }
}
```

### Error Handling

```javascript
import { ApiError, ErrorCodes } from '@/core/api/types'
import { getErrorMessage, isValidationError } from '@/core/utils/errors'

try {
  await jobsService.create(data)
} catch (error) {
  if (error instanceof ApiError) {
    if (error.isValidationError()) {
      // Handle validation errors
      console.error('Validation errors:', error.details)
    } else if (error.isNotFound()) {
      // Handle not found
      console.error('Resource not found')
    } else {
      // Handle other errors
      console.error(getErrorMessage(error))
    }
  }
}
```

## Backward Compatibility

The API maintains backward compatibility during the refactoring phase. Old response formats are still supported, but new code should use the standard format.
