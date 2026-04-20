import { test, expect } from '@playwright/test';

test.describe('Registration Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should display registration form with email, password, nickname fields', async ({ page }) => {
    await expect(page.getByTestId('register-inp-email')).toBeVisible();
    await expect(page.getByTestId('register-inp-password')).toBeVisible();
    await expect(page.getByTestId('register-inp-nickname')).toBeVisible();
    await expect(page.getByTestId('register-btn-submit')).toBeVisible();
  });

  test('should register successfully and redirect to login', async ({ page }) => {
    await page.getByTestId('register-inp-email').fill('test@example.com');
    await page.getByTestId('register-inp-nickname').fill('测试用户');
    await page.getByTestId('register-inp-password').fill('Password123');
    await page.getByTestId('register-btn-submit').click();
    await expect(page).toHaveURL(/.*login/);
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.getByTestId('register-inp-email').fill('invalid-email');
    await page.getByTestId('register-inp-nickname').fill('用户');
    await page.getByTestId('register-inp-password').fill('Password123');
    await page.getByTestId('register-btn-submit').click();
    await expect(page.getByText(/邮箱.*格式/)).toBeVisible();
  });

  test('should show validation error for short password', async ({ page }) => {
    await page.getByTestId('register-inp-email').fill('test@example.com');
    await page.getByTestId('register-inp-nickname').fill('用户');
    await page.getByTestId('register-inp-password').fill('123');
    await page.getByTestId('register-btn-submit').click();
    await expect(page.getByText(/密码.*[短少]/)).toBeVisible();
  });

  test('should show validation error for short nickname', async ({ page }) => {
    await page.getByTestId('register-inp-email').fill('test@example.com');
    await page.getByTestId('register-inp-nickname').fill('a');
    await page.getByTestId('register-inp-password').fill('Password123');
    await page.getByTestId('register-btn-submit').click();
    await expect(page.getByText(/昵称.*[短少]/)).toBeVisible();
  });

  test('should show error for duplicate email', async ({ page }) => {
    await page.getByTestId('register-inp-email').fill('exist@example.com');
    await page.getByTestId('register-inp-nickname').fill('用户');
    await page.getByTestId('register-inp-password').fill('Password123');
    await page.getByTestId('register-btn-submit').click();
    await expect(page.getByText(/邮箱已注册/)).toBeVisible();
  });

  test('should navigate to login page via link', async ({ page }) => {
    await page.getByTestId('register-link-login').click();
    await expect(page).toHaveURL(/.*login/);
  });
});

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form with email, password, remember checkbox', async ({ page }) => {
    await expect(page.getByTestId('login-inp-email')).toBeVisible();
    await expect(page.getByTestId('login-inp-password')).toBeVisible();
    await expect(page.getByTestId('login-chk-remember')).toBeVisible();
    await expect(page.getByTestId('login-btn-submit')).toBeVisible();
  });

  test('should login successfully and redirect to dashboard', async ({ page }) => {
    await page.getByTestId('login-inp-email').fill('test@example.com');
    await page.getByTestId('login-inp-password').fill('Password123');
    await page.getByTestId('login-btn-submit').click();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show error for wrong credentials', async ({ page }) => {
    await page.getByTestId('login-inp-email').fill('test@example.com');
    await page.getByTestId('login-inp-password').fill('WrongPassword');
    await page.getByTestId('login-btn-submit').click();
    await expect(page.getByText(/邮箱或密码错误/)).toBeVisible();
  });

  test('should show error for unverified email', async ({ page }) => {
    await page.getByTestId('login-inp-email').fill('unverified@example.com');
    await page.getByTestId('login-inp-password').fill('Password123');
    await page.getByTestId('login-btn-submit').click();
    await expect(page.getByText(/邮箱未验证/)).toBeVisible();
  });

  test('should remember login state when checkbox is checked', async ({ context, page }) => {
    await page.getByTestId('login-inp-email').fill('test@example.com');
    await page.getByTestId('login-inp-password').fill('Password123');
    await page.getByTestId('login-chk-remember').check();
    await page.getByTestId('login-btn-submit').click();
    await expect(page).toHaveURL(/.*dashboard/);

    const newPage = await context.newPage();
    await newPage.goto('/dashboard');
    await expect(newPage).toHaveURL(/.*dashboard/);
    await newPage.close();
  });

  test('should navigate to register page', async ({ page }) => {
    await page.getByTestId('login-link-register').click();
    await expect(page).toHaveURL(/.*register/);
  });

  test('should navigate to forgot password page', async ({ page }) => {
    await page.getByTestId('login-link-forgot').click();
    await expect(page).toHaveURL(/.*forgot-password/);
  });
});

test.describe('Forgot Password Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/forgot-password');
  });

  test('should display email input', async ({ page }) => {
    await expect(page.getByTestId('forgot-inp-email')).toBeVisible();
    await expect(page.getByTestId('forgot-btn-submit')).toBeVisible();
  });

  test('should show success message after submit', async ({ page }) => {
    await page.getByTestId('forgot-inp-email').fill('test@example.com');
    await page.getByTestId('forgot-btn-submit').click();
    await expect(page.getByText(/重置邮件已发送/)).toBeVisible();
  });

  test('should show success message for non-existent user without revealing existence', async ({ page }) => {
    await page.getByTestId('forgot-inp-email').fill('nobody@example.com');
    await page.getByTestId('forgot-btn-submit').click();
    await expect(page.getByText(/重置邮件已发送/)).toBeVisible();
  });

  test('should show validation error for invalid email', async ({ page }) => {
    await page.getByTestId('forgot-inp-email').fill('invalid-email');
    await page.getByTestId('forgot-btn-submit').click();
    await expect(page.getByText(/邮箱.*格式/)).toBeVisible();
  });

  test('should navigate back to login', async ({ page }) => {
    await page.getByTestId('forgot-link-login').click();
    await expect(page).toHaveURL(/.*login/);
  });
});

test.describe('Reset Password Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/reset-password?token=valid-test-token');
  });

  test('should display password and confirm fields', async ({ page }) => {
    await expect(page.getByTestId('reset-inp-password')).toBeVisible();
    await expect(page.getByTestId('reset-inp-confirm')).toBeVisible();
    await expect(page.getByTestId('reset-btn-submit')).toBeVisible();
  });

  test('should reset password successfully and redirect to login', async ({ page }) => {
    await page.getByTestId('reset-inp-password').fill('NewPassword456');
    await page.getByTestId('reset-inp-confirm').fill('NewPassword456');
    await page.getByTestId('reset-btn-submit').click();
    await expect(page).toHaveURL(/.*login/);
  });

  test('should show error when passwords do not match', async ({ page }) => {
    await page.getByTestId('reset-inp-password').fill('NewPassword456');
    await page.getByTestId('reset-inp-confirm').fill('Different789');
    await page.getByTestId('reset-btn-submit').click();
    await expect(page.getByText(/密码.*一致/)).toBeVisible();
  });

  test('should show error for short password', async ({ page }) => {
    await page.getByTestId('reset-inp-password').fill('123');
    await page.getByTestId('reset-inp-confirm').fill('123');
    await page.getByTestId('reset-btn-submit').click();
    await expect(page.getByText(/密码.*[短少]/)).toBeVisible();
  });

  test('should show error for invalid or expired token', async ({ page }) => {
    await page.goto('/reset-password?token=invalid-token');
    await page.getByTestId('reset-inp-password').fill('NewPassword456');
    await page.getByTestId('reset-inp-confirm').fill('NewPassword456');
    await page.getByTestId('reset-btn-submit').click();
    await expect(page.getByText(/链接无效或已过期/)).toBeVisible();
  });
});
