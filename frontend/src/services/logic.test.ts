import { describe, expect, it } from 'vitest'
import { monthlyEquivalent, parseCsv, validateCsvRow } from './logic'

const categories = [{ id: 'food', name: 'Food' }, { id: 'software', name: 'Software' }]

describe('monthlyEquivalent', () => {
  it('keeps monthly amounts in integer cents', () => expect(monthlyEquivalent(1599, 'monthly')).toBe(1599))
  it('rounds yearly and weekly conversions once at the end', () => {
    expect(monthlyEquivalent(12000, 'yearly')).toBe(1000)
    expect(monthlyEquivalent(1000, 'weekly')).toBe(4333)
  })
})

describe('CSV validation and parsing', () => {
  it('rejects invalid date, amount, and category values', () => {
    expect(validateCsvRow(['10/01/2026', 'Coffee', '4.50', 'Food'], categories)).toContain('YYYY-MM-DD')
    expect(validateCsvRow(['2026-10-01', 'Coffee', '-1', 'Food'], categories)).toContain('positive')
    expect(validateCsvRow(['2026-10-01', 'Coffee', '4.50', 'Travel'], categories)).toBe('Unknown category')
  })
  it('imports valid rows without failing on bad rows', () => {
    const parsed = parseCsv('date,description,amount,category\n2026-10-01,Coffee,4.50,Food\nnope,Missing,2,Food\n2026-10-02,Editor,10,Software', categories)
    expect(parsed.result).toEqual({ imported: 2, rejected: [{ row: 3, reason: 'Date must be YYYY-MM-DD' }] })
    expect(parsed.rows[0].amountCents).toBe(450)
  })
})
