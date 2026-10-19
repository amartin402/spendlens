export * from './types'
export * from './logic'
import { apiService } from './api'
import { mockService } from './mock'

export { apiService, mockService }
export const service = import.meta.env.VITE_USE_MOCK === 'true' ? mockService : apiService
