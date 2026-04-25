import { test, expect } from './fixtures/auth';

test.describe('Dashboard / Personal Center', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/dashboard');
  });

  test('E2E-DASH-001: should display my teams list', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-teams').click();
    await expect(page.getByTestId('dashboard-list-my-teams')).toBeVisible();
  });

  test('E2E-DASH-002: should create team from teams page', async ({ authenticatedPage: page }) => {
    await page.goto('/teams');
    await page.getByTestId('team-list-btn-create').click();

    const dialog = page.getByTestId('team-list-dlg-create');
    await expect(dialog).toBeVisible();

    const teamName = `E2E Team ${Date.now()}`;
    await dialog.getByTestId('team-list-dlg-create-inp-name').fill(teamName);
    await dialog.getByTestId('team-list-dlg-create-txtarea-desc').fill('E2E test team description');
    await dialog.getByTestId('team-list-dlg-create-btn-submit').click();

    await expect(dialog).not.toBeVisible();
  });

  test('should display user nickname and email', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-txt-nickname')).toBeVisible();
    await expect(page.getByTestId('dashboard-txt-email')).toBeVisible();
  });

  test('E2E-DASH-003: should display pending reviews', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-pending').click();
    await page.getByTestId('dashboard-tab-pending-reviews').click();
    await expect(page.getByTestId('dashboard-list-pending-reviews')).toBeVisible();
  });

  test('E2E-DASH-004: should display pending tasks', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-pending').click();
    await page.getByTestId('dashboard-tab-pending-tasks').click();
    await expect(page.getByTestId('dashboard-list-pending-tasks')).toBeVisible();
  });

  test('E2E-DASH-005: should accept invitation from dashboard', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-pending').click();
    await page.getByTestId('dashboard-tab-pending-invitations').click();
    await expect(page.getByTestId('dashboard-list-pending-invitations')).toBeVisible();

    const acceptBtn = page.getByTestId(/dashboard-btn-accept-invitation-/).first();
    if (await acceptBtn.isVisible()) {
      await acceptBtn.click();
      await expect(acceptBtn).not.toBeVisible();
    }
  });

  test('E2E-DASH-006: should reject invitation from dashboard', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-pending').click();
    await page.getByTestId('dashboard-tab-pending-invitations').click();
    await expect(page.getByTestId('dashboard-list-pending-invitations')).toBeVisible();

    const rejectBtn = page.getByTestId(/dashboard-btn-reject-invitation-/).first();
    if (await rejectBtn.isVisible()) {
      await rejectBtn.click();
      await expect(rejectBtn).not.toBeVisible();
    }
  });

  test('E2E-DASH-007: should update nickname', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-profile').click();

    const nicknameInput = page.getByTestId('dashboard-inp-nickname');
    await nicknameInput.clear();
    await nicknameInput.fill('新昵称');

    await page.getByTestId('dashboard-btn-save-profile').click();

    await expect(page.getByText(/保存成功/)).toBeVisible();
  });

  test('E2E-DASH-008: should change password successfully', async ({ authenticatedPage: page }) => {
    const testEmail = `pwdtest_${Date.now()}@test.com`
    const testPassword = 'Test1234!'
    await page.request.post('/api/v1/auth/register', {
      data: { email: testEmail, password: testPassword, nickname: `pwdtest_${Date.now()}` },
    })
    const loginResp = await page.request.post('/api/v1/auth/login', {
      data: { email: testEmail, password: testPassword },
    })
    const loginBody = await loginResp.json()
    const token = loginBody.data.token
    await page.evaluate((t: string) => localStorage.setItem('token', t), token)
    const context = page.context()
    await context.addCookies([{ name: 'token', value: token, domain: 'localhost', path: '/' }])

    await page.goto('/dashboard')
    await page.getByTestId('dashboard-tab-profile').click()
    await page.getByTestId('dashboard-btn-change-password').click()

    await expect(page.getByTestId('dashboard-dlg-password')).toBeVisible()

    await page.getByTestId('dashboard-dlg-password-inp-old').fill(testPassword)
    await page.getByTestId('dashboard-dlg-password-inp-new').fill('NewPassword567!')
    await page.getByTestId('dashboard-dlg-password-inp-confirm').fill('NewPassword567!')
    await page.getByTestId('dashboard-dlg-password-btn-submit').click()

    await expect(page.getByText(/密码修改成功/)).toBeVisible()
  })

  test('E2E-DASH-009: should show error for wrong old password', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-profile').click()
    await page.getByTestId('dashboard-btn-change-password').click()

    await page.getByTestId('dashboard-dlg-password-inp-old').fill('WrongOldPassword')
    await page.getByTestId('dashboard-dlg-password-inp-new').fill('NewPassword567!')
    await page.getByTestId('dashboard-dlg-password-inp-confirm').fill('NewPassword567!')
    await page.getByTestId('dashboard-dlg-password-btn-submit').click()

    await expect(page.getByText(/旧密码错误/)).toBeVisible()
  });

  test('should show empty state when no pending items', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-tab-pending').click();
    await page.getByTestId('dashboard-tab-pending-reviews').click();
    const reviews = page.getByTestId('dashboard-list-pending-reviews');
    await expect(reviews.getByText(/暂无|没有|为空/)).toBeVisible();

    await page.getByTestId('dashboard-tab-pending-tasks').click();
    const tasks = page.getByTestId('dashboard-list-pending-tasks');
    await expect(tasks.getByText(/暂无|没有|为空/)).toBeVisible();

    await page.getByTestId('dashboard-tab-pending-invitations').click();
    const invitations = page.getByTestId('dashboard-list-pending-invitations');
    await expect(invitations.getByText(/暂无|没有|为空/)).toBeVisible();
  });
});
