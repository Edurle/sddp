import { test, expect } from './fixtures/auth';

test.describe('Dashboard / Personal Center', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/dashboard');
  });

  test('should display user nickname and email', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-txt-nickname')).toBeVisible();
    await expect(page.getByTestId('dashboard-txt-email')).toBeVisible();
  });

  test('should navigate to change password', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-link-change-password').click();
    await expect(page).toHaveURL(/.*change-password/);
  });

  test('should navigate to edit profile', async ({ authenticatedPage: page }) => {
    await page.getByTestId('dashboard-link-edit-profile').click();
    await expect(page).toHaveURL(/.*edit-profile/);
  });

  test('should display pending reviews list', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-list-pending-reviews')).toBeVisible();
  });

  test('should display pending tasks list', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-list-pending-tasks')).toBeVisible();
  });

  test('should display pending invitations list', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-list-pending-invitations')).toBeVisible();
  });

  test('should show empty state when no pending items', async ({ authenticatedPage: page }) => {
    const reviews = page.getByTestId('dashboard-list-pending-reviews');
    const tasks = page.getByTestId('dashboard-list-pending-tasks');
    const invitations = page.getByTestId('dashboard-list-pending-invitations');
    await expect(reviews.getByText(/暂无|没有|为空/)).toBeVisible();
    await expect(tasks.getByText(/暂无|没有|为空/)).toBeVisible();
    await expect(invitations.getByText(/暂无|没有|为空/)).toBeVisible();
  });

  test('should accept invitation from dashboard', async ({ authenticatedPage: page }) => {
    const invitation = page.getByTestId(/dashboard-btn-accept-invitation-/).first();
    if (await invitation.isVisible()) {
      await invitation.click();
      await expect(invitation).not.toBeVisible();
    }
  });
});
