import type { Category, CsvResult, MonthlyReport, SpendLensService, Subscription, Transaction, TrendPoint } from './types'

const apiUrl = import.meta.env.VITE_API_URL ?? '/api'
const tokenKey = 'spendlens-access-token'
let loginPromise: Promise<string | undefined> | undefined

type AuthResponse = { access_token: string }

const storedToken = () => {
  const configured = import.meta.env.VITE_API_TOKEN
  if (configured) return configured
  return localStorage.getItem(tokenKey) ?? undefined
}

const errorMessage = async (response: Response) => {
  try {
    const data = await response.json() as { error?: { message?: string } }
    return data.error?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

const authenticate = async (): Promise<string | undefined> => {
  const existing = storedToken()
  if (existing) return existing
  const email = import.meta.env.VITE_API_EMAIL
  const password = import.meta.env.VITE_API_PASSWORD
  if (!email || !password) return undefined
  const response = await fetch(`${apiUrl}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  const data = await response.json() as AuthResponse
  localStorage.setItem(tokenKey, data.access_token)
  return data.access_token
}

const accessToken = () => {
  loginPromise ??= authenticate().finally(() => { loginPromise = undefined })
  return loginPromise
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await accessToken()
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${apiUrl}${path}`, { ...init, headers })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const apiService: SpendLensService = {
  getCategories: () => request<Category[]>('/categories'),
  getTransactions: async () => (await request<{ items: Transaction[] }>('/transactions?page_size=100')).items,
  addTransaction: (input) => request<Transaction>('/transactions', json(input)),
  deleteTransaction: (id) => request<void>(`/transactions/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  getSubscriptions: () => request<Subscription[]>('/subscriptions'),
  addSubscription: (input) => request<Subscription>('/subscriptions', json(input)),
  cancelSubscription: (id) => request<void>(`/subscriptions/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'cancelled' }),
  }),
  getMonthlyReport: (month) => request<MonthlyReport>(`/reports/monthly?month=${encodeURIComponent(month)}`),
  getTrend: (months) => request<TrendPoint[]>(`/reports/trend?months=${months}`),
  importCsv: (csv) => request<CsvResult>('/transactions/import', {
    method: 'POST',
    headers: { 'Content-Type': 'text/csv' },
    body: csv,
  }),
}
