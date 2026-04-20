import { test, expect } from './fixtures/auth'

const TEAM_ID = 'test-team-id'
const CUSTOM_ROLE_ID = 'role-custom-1'
const BUILT_IN_ROLE_ID = 'role-owner'

test.beforeEach(async ({ authenticatedPage }) => {
  await authenticatedPage.goto(`/teams/${TEAM_ID}`)
  await authenticatedPage.getByTestId('team-detail-tab-roles').click()
})

test.describe('Role List', () => {
  test('E2E-ROLE-001: should display built-in roles', async ({ authenticatedPage }) => {
    const table = authenticatedPage.getByTestId('team-roles-tbl-roles')
    await expect(table).toBeVisible()

    await expect(table.getByText('团队所有者')).toBeVisible()
    await expect(table.getByText('团队管理员')).toBeVisible()
  })

  test('E2E-ROLE-001: should display custom roles', async ({ authenticatedPage }) => {
    const table = authenticatedPage.getByTestId('team-roles-tbl-roles')
    await expect(table).toBeVisible()

    const customRoleRow = table.locator('tr', { hasText: '开发者' })
    await expect(customRoleRow).toBeVisible()
  })
})

test.describe('Create Role', () => {
  test('E2E-ROLE-002: should open create role dialog', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-roles-btn-create').click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit-inp-name')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit-txtarea-desc')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit-btn-save')).toBeVisible()
  })

  test('E2E-ROLE-002: should create role with name and permissions', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-roles-btn-create').click()

    await authenticatedPage.getByTestId('team-roles-dlg-edit-inp-name').fill('开发者')
    await authenticatedPage.getByTestId('team-roles-dlg-edit-txtarea-desc').fill('开发团队成员')
    await authenticatedPage.getByTestId('team-roles-dlg-edit-chk-permission-task:create').check()
    await authenticatedPage.getByTestId('team-roles-dlg-edit-chk-permission-task:edit').check()

    await authenticatedPage.getByTestId('team-roles-dlg-edit-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit')).not.toBeVisible()
    await expect(authenticatedPage.getByTestId('team-roles-tbl-roles').getByText('开发者')).toBeVisible()
  })

  test('E2E-ROLE-003: should show error for duplicate role name', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-roles-btn-create').click()

    await authenticatedPage.getByTestId('team-roles-dlg-edit-inp-name').fill('开发者')

    await authenticatedPage.getByTestId('team-roles-dlg-edit-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit-txt-error')).toContainText('角色名称已存在')
  })
})

test.describe('Edit Role', () => {
  test('E2E-ROLE-004: should edit role name and permissions', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-roles-btn-edit-${CUSTOM_ROLE_ID}`).click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit')).toBeVisible()

    const nameInput = authenticatedPage.getByTestId('team-roles-dlg-edit-inp-name')
    await nameInput.clear()
    await nameInput.fill('高级开发者')

    await authenticatedPage.getByTestId('team-roles-dlg-edit-chk-permission-task:delete').check()

    await authenticatedPage.getByTestId('team-roles-dlg-edit-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-edit')).not.toBeVisible()
    await expect(authenticatedPage.getByTestId('team-roles-tbl-roles').getByText('高级开发者')).toBeVisible()
  })

  test('E2E-ROLE-005: cannot edit built-in roles', async ({ authenticatedPage }) => {
    const editBtn = authenticatedPage.getByTestId(`team-roles-btn-edit-${BUILT_IN_ROLE_ID}`)
    await expect(editBtn).not.toBeVisible()
  })
})

test.describe('Delete Role', () => {
  test('E2E-ROLE-006: should delete custom role', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-roles-btn-delete-${CUSTOM_ROLE_ID}`).click()

    await expect(authenticatedPage.getByTestId('team-roles-dlg-confirm')).toBeVisible()
    await authenticatedPage.getByTestId('team-roles-dlg-confirm-btn-confirm').click()

    await expect(authenticatedPage.getByTestId(`team-roles-btn-delete-${CUSTOM_ROLE_ID}`)).not.toBeVisible()
  })

  test('E2E-ROLE-005: cannot delete built-in roles', async ({ authenticatedPage }) => {
    const deleteBtn = authenticatedPage.getByTestId(`team-roles-btn-delete-${BUILT_IN_ROLE_ID}`)
    await expect(deleteBtn).not.toBeVisible()
  })
})
