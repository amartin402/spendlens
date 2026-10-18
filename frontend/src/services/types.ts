export type BillingPeriod = 'weekly' | 'monthly' | 'yearly'
export type Category = { id: string; name: string }
export type Transaction = { id: string; date: string; description: string; amountCents: number; categoryId: string; source: 'manual' | 'csv' }
export type Subscription = { id: string; name: string; amountCents: number; billingPeriod: BillingPeriod; nextRenewalDate: string; categoryId: string; status: 'active' | 'cancelled' }
export type MonthlyReport = { totalCents: number; subscriptionCents: number; categories: { name: string; totalCents: number; color: string }[]; topMerchants: { name: string; totalCents: number }[] }
export type TrendPoint = { month: string; label: string; totalCents: number; subscriptionCents: number }
export type CsvResult = { imported: number; rejected: { row: number; reason: string }[] }
export type SpendLensService = { getCategories(): Promise<Category[]>; getTransactions(): Promise<Transaction[]>; addTransaction(input: Omit<Transaction, 'id' | 'source'> & { source?: Transaction['source'] }): Promise<Transaction>; deleteTransaction(id: string): Promise<void>; getSubscriptions(): Promise<Subscription[]>; addSubscription(input: Omit<Subscription, 'id' | 'status'>): Promise<Subscription>; cancelSubscription(id: string): Promise<void>; getMonthlyReport(month: string): Promise<MonthlyReport>; getTrend(months: number): Promise<TrendPoint[]>; importCsv(csv: string): Promise<CsvResult> }
