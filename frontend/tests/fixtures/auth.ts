import { test as base, expect } from '@playwright/test'

interface AuthFixtures {
  authenticatedPage: import('@playwright/test').Page
}

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const loginResponse = await page.request.post('/api/v1/auth/login', {
      data: {
        email: 'admin@example.com',
        password: 'Admin1234!',
      },
    })

    const loginBody = await loginResponse.json()
    const token = loginBody.data.token

    await page.goto('/')
    await page.evaluate((accessToken) => {
      localStorage.setItem('token', accessToken)
    }, token)

    const context = page.context()
    await context.addCookies([{
      name: 'token',
      value: token,
      domain: 'localhost',
      path: '/',
    }])

    await page.goto('/dashboard')
    await use(page)
  },
})

export { expect }
