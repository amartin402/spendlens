import type { BillingPeriod, Category, CsvResult, Subscription, Transaction } from './types'

export const monthlyEquivalent = (amountCents: number, period: BillingPeriod) => period === 'monthly' ? amountCents : period === 'yearly' ? Math.round(amountCents / 12) : Math.round(amountCents * 52 / 12)
export const monthOf = (date: string) => date.slice(0, 7)
export function validateCsvRow(row: string[], categories: Category[]) {
  if (row.length < 4) return 'Expected date, description, amount, category'
  if (!/^\d{4}-\d{2}-\d{2}$/.test(row[0]) || Number.isNaN(Date.parse(row[0]))) return 'Date must be YYYY-MM-DD'
  if (!row[1].trim()) return 'Description is required'
  if (!/^\d+(\.\d{1,2})?$/.test(row[2].trim()) || Number(row[2]) <= 0) return 'Amount must be a positive number'
  if (!categories.some(c => c.name.toLowerCase() === row[3].trim().toLowerCase())) return 'Unknown category'
  return null
}
export function parseCsv(csv: string, categories: Category[]): { rows: Omit<Transaction, 'id' | 'source'>[]; result: CsvResult } {
  const lines = csv.trim().split(/\r?\n/).filter(Boolean); const rows: Omit<Transaction, 'id' | 'source'>[] = []; const rejected: CsvResult['rejected'] = []
  lines.slice(1).forEach((line, index) => { const cells = line.split(',').map(cell => cell.trim()); const reason = validateCsvRow(cells, categories); if (reason) rejected.push({ row: index + 2, reason }); else rows.push({ date: cells[0], description: cells[1], amountCents: Math.round(Number(cells[2]) * 100), categoryId: categories.find(c => c.name.toLowerCase() === cells[3].toLowerCase())!.id }) })
  return { rows, result: { imported: rows.length, rejected } }
}
