import { test as base, expect } from '@playwright/test'

interface AuthFixtures {
  authenticatedPage: import('@playwright/test').Page
}

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const testEmail = `e2e_${Date.now()}@test.com`
    const testPassword = 'Test1234!'
    const testNickname = `e2e_user_${Date.now()}`

    await page.request.post('/api/v1/auth/register', {
      data: {
        email: testEmail,
        password: testPassword,
        nickname: testNickname,
      },
    })

    const loginResponse = await page.request.post('/api/v1/auth/login', {
      data: {
        email: testEmail,
        password: testPassword,
      },
    })

    const loginBody = await loginResponse.json()
    const token = loginBody.access_token

    await page.evaluate((accessToken) => {
      localStorage.setItem('token', accessToken)
    }, token)

    await page.goto('/dashboard')
    await use(page)
  },
})

export { expect }
