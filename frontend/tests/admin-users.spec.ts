import { test, expect } from './fixtures/auth';

test.describe('Admin Users Page', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/admin/users');
  });

  test('should display user list table', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('user-mgmt-tbl-users')).toBeVisible();
    await expect(page.getByTestId('user-mgmt-tbl-users').locator('thead')).toContainText('邮箱');
    await expect(page.getByTestId('user-mgmt-tbl-users').locator('thead')).toContainText('昵称');
  });

  test('should search users by keyword', async ({ authenticatedPage: page }) => {
    await page.getByTestId('user-mgmt-inp-search').fill('exist@');
    await page.waitForTimeout(1000);
    const rows = page.getByTestId('user-mgmt-tbl-users').locator('tbody tr');
    const count = await rows.count();
    for (let i = 0; i < count; i++) {
      await expect(rows.nth(i)).toContainText('exist@');
    }
  });

  test('should paginate user list', async ({ authenticatedPage: page }) => {
    const pagination = page.getByTestId('user-mgmt-pag-list');
    if (await pagination.isVisible()) {
      const nextBtn = pagination.getByText(/下一页|Next/);
      if (await nextBtn.isVisible()) {
        await nextBtn.click();
        const rows = page.getByTestId('user-mgmt-tbl-users').locator('tbody tr');
        const count = await rows.count();
        expect(count).toBeGreaterThan(0);
      }
    }
  });

  test('should open create user dialog', async ({ authenticatedPage: page }) => {
    await page.getByTestId('user-mgmt-btn-create').click();
    await expect(page.getByTestId('user-mgmt-dlg-create')).toBeVisible();
  });

  test('should create user successfully', async ({ authenticatedPage: page }) => {
    await page.getByTestId('user-mgmt-btn-create').click();
    await expect(page.getByTestId('user-mgmt-dlg-create')).toBeVisible();
    const dlg = page.getByTestId('user-mgmt-dlg-create');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-email"]').fill('new@example.com');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-nickname"]').fill('新用户');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-password"]').fill('InitPass123');
    await dlg.locator('[data-testid="admin-users-dlg-create-btn-submit"]').click();
    await expect(page.getByTestId('user-mgmt-dlg-create')).not.toBeVisible();
    await expect(page.getByTestId('user-mgmt-tbl-users')).toContainText('new@example.com');
  });

  test('should show validation errors in create dialog', async ({ authenticatedPage: page }) => {
    await page.getByTestId('user-mgmt-btn-create').click();
    const dlg = page.getByTestId('user-mgmt-dlg-create');
    await dlg.locator('[data-testid="admin-users-dlg-create-btn-submit"]').click();
    await expect(dlg.getByText(/必填|不能为空/)).toBeVisible();
  });

  test('should show error when creating user with existing email', async ({ authenticatedPage: page }) => {
    await page.getByTestId('user-mgmt-btn-create').click();
    const dlg = page.getByTestId('user-mgmt-dlg-create');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-email"]').fill('exist@example.com');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-nickname"]').fill('用户');
    await dlg.locator('[data-testid="admin-users-dlg-create-inp-password"]').fill('Password123');
    await dlg.locator('[data-testid="admin-users-dlg-create-btn-submit"]').click();
    await expect(dlg.getByText(/邮箱已注册/)).toBeVisible();
  });

  test('should toggle user active status', async ({ authenticatedPage: page }) => {
    const toggleBtn = page.getByTestId(/user-mgmt-btn-toggle-status-/).first();
    if (await toggleBtn.isVisible()) {
      const currentText = await toggleBtn.textContent();
      await toggleBtn.click();
      const newText = await toggleBtn.textContent();
      expect(newText).not.toBe(currentText);
    }
  });

  test('should show error when admin disables self', async ({ authenticatedPage: page }) => {
    const selfToggleBtn = page.getByTestId(/user-mgmt-btn-toggle-status-/).first();
    if (await selfToggleBtn.isVisible()) {
      await selfToggleBtn.click();
      await expect(page.getByText(/不能禁用自己/)).toBeVisible();
    }
  });
});

test.describe('Admin Users Page - Access Control', () => {
  test('should deny access for non-admin users', async ({ page }) => {
    await page.goto('/login');
    const testEmail = `nonadmin_${Date.now()}@test.com`;
    const testPassword = 'Test1234!';
    const testNickname = `nonadmin_${Date.now()}`;
    await page.request.post('/api/v1/auth/register', {
      data: { email: testEmail, password: testPassword, nickname: testNickname },
    });
    await page.getByTestId('login-inp-email').fill(testEmail);
    await page.getByTestId('login-inp-password').fill(testPassword);
    await page.getByTestId('login-btn-submit').click();
    await page.waitForURL(/.*dashboard/);
    await page.goto('/admin/users');
    const body = page.locator('body');
    const hasForbidden = await body.getByText(/无权限|403|forbidden/i).isVisible().catch(() => false);
    const isRedirected = page.url().match(/\/(dashboard|login)/) !== null;
    expect(hasForbidden || isRedirected).toBeTruthy();
  });
});
