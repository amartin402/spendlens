import { expect, test } from '@playwright/test'

test('a user can track spending and cannot see another user data', async ({ page }) => {
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`
  const firstEmail = `e2e-first-${suffix}@example.com`
  const secondEmail = `e2e-second-${suffix}@example.com`
  const password = 'e2e-password-123'
  const description = `E2E transaction ${suffix}`
  const subscriptionName = `E2E annual plan ${suffix}`

  await page.goto('/')
  await page.getByLabel('Email').fill(firstEmail)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Good morning, Jordan.' })).toBeVisible()

  await page.getByRole('button', { name: /Transactions/ }).click()
  await page.getByRole('button', { name: '+ Add transaction' }).click()
  await page.locator('input[name="date"]').fill('2026-10-20')
  await page.locator('input[name="description"]').fill(description)
  await page.locator('input[name="amount"]').fill('12.34')
  await page.locator('select[name="category"]').selectOption({ label: 'Food' })
  await page.getByRole('button', { name: /Add transaction/ }).last().click()

  await page.getByRole('button', { name: /Overview/ }).click()
  await expect(page.getByText('$12.34', { exact: true }).first()).toBeVisible()

  await page.getByRole('button', { name: /Subscriptions/ }).click()
  await page.getByRole('button', { name: '+ Add subscription' }).click()
  await page.locator('input[name="name"]').fill(subscriptionName)
  await page.locator('input[name="amount"]').fill('120')
  await page.locator('select[name="period"]').selectOption('yearly')
  await page.locator('input[name="date"]').fill('2026-12-20')
  await page.locator('select[name="category"]').selectOption({ label: 'Software' })
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('$10.00', { exact: true }).first()).toBeVisible()

  await page.getByRole('button', { name: /Sign out/ }).click()
  await expect(page.getByRole('button', { name: 'Register', exact: true })).toBeVisible()
  await page.getByLabel('Email').fill(secondEmail)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Register', exact: true }).click()

  await expect(page.getByText(description, { exact: true })).toHaveCount(0)
  await expect(page.getByText(subscriptionName, { exact: true })).toHaveCount(0)
})
