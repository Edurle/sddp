import { test, expect } from './fixtures/auth'

const TEAM_ID = 'test-team-id'
const TARGET_USER_ID = 'user-123'
const TARGET_ROLE_ID = 'role-dev'

test.beforeEach(async ({ authenticatedPage }) => {
  await authenticatedPage.goto(`/teams/${TEAM_ID}`)
  await authenticatedPage.getByTestId('team-detail-tab-members').click()
})

test.describe('Member List', () => {
  test('E2E-MEMBER-003: should display member list with nickname, email, and roles', async ({ authenticatedPage }) => {
    const table = authenticatedPage.getByTestId('team-members-tbl-members')
    await expect(table).toBeVisible()

    const rows = table.locator('tbody tr')
    await expect(rows.first()).toBeVisible()

    await expect(rows.first().getByTestId('team-members-txt-nickname')).toBeVisible()
    await expect(rows.first().getByTestId('team-members-txt-email')).toBeVisible()
    await expect(rows.first().getByTestId('team-members-txt-roles')).toBeVisible()
  })

  test('E2E-MEMBER-003: should filter members by role', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-members-sel-role-filter').selectOption({ index: 1 })

    const rows = authenticatedPage.getByTestId('team-members-tbl-members').locator('tbody tr')
    const count = await rows.count()
    for (let i = 0; i < count; i++) {
      await expect(rows.nth(i).getByTestId('team-members-txt-roles')).toContainText('团队管理员')
    }
  })
})

test.describe('Invite Member', () => {
  test('E2E-MEMBER-001: should open invite dialog', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-members-btn-invite').click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-invite')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-members-dlg-invite-inp-identifier')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-members-dlg-invite-btn-submit')).toBeVisible()
  })

  test('E2E-MEMBER-001: should invite member by email successfully', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-members-btn-invite').click()

    await authenticatedPage.getByTestId('team-members-dlg-invite-inp-identifier').fill('newuser@example.com')
    await authenticatedPage.getByTestId('team-members-dlg-invite-btn-submit').click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-invite')).not.toBeVisible()
    await expect(authenticatedPage.getByTestId('team-members-txt-success')).toContainText('邀请已发送')
  })

  test('E2E-MEMBER-002: should show error for non-existent user', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-members-btn-invite').click()

    await authenticatedPage.getByTestId('team-members-dlg-invite-inp-identifier').fill('nonexistent@example.com')
    await authenticatedPage.getByTestId('team-members-dlg-invite-btn-submit').click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-invite-txt-error')).toContainText('用户不存在')
  })

  test('E2E-MEMBER-002: should show error for already-member user', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-members-btn-invite').click()

    await authenticatedPage.getByTestId('team-members-dlg-invite-inp-identifier').fill('existingmember@example.com')
    await authenticatedPage.getByTestId('team-members-dlg-invite-btn-submit').click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-invite-txt-error')).toContainText('用户已在团队中')
  })
})

test.describe('Remove Member', () => {
  test('E2E-MEMBER-004: should remove member successfully', async ({ authenticatedPage }) => {
    const removeBtn = authenticatedPage.getByTestId(`team-members-btn-remove-${TARGET_USER_ID}`)
    await removeBtn.click()

    await authenticatedPage.getByTestId('team-members-dlg-confirm-btn-confirm').click()

    await expect(authenticatedPage.getByTestId(`team-members-btn-remove-${TARGET_USER_ID}`)).not.toBeVisible()
  })

  test('E2E-MEMBER-004: should confirm removal before deleting', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-members-btn-remove-${TARGET_USER_ID}`).click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-confirm')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-members-dlg-confirm-btn-confirm')).toBeVisible()
  })

  test('cannot remove team owner', async ({ authenticatedPage }) => {
    const ownerRemoveBtn = authenticatedPage.getByTestId('team-members-btn-remove-owner')
    await expect(ownerRemoveBtn).not.toBeVisible()
  })
})

test.describe('Assign Roles', () => {
  test('E2E-MEMBER-005: should open role assignment dialog', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-members-btn-roles-${TARGET_USER_ID}`).click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-roles')).toBeVisible()
  })

  test('E2E-MEMBER-005: should select multiple roles', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-members-btn-roles-${TARGET_USER_ID}`).click()

    await authenticatedPage.getByTestId(`team-members-dlg-roles-chk-role-${TARGET_ROLE_ID}`).check()
    await authenticatedPage.getByTestId('team-members-dlg-roles-chk-role-role-admin').check()

    await expect(authenticatedPage.getByTestId(`team-members-dlg-roles-chk-role-${TARGET_ROLE_ID}`)).toBeChecked()
    await expect(authenticatedPage.getByTestId('team-members-dlg-roles-chk-role-role-admin')).toBeChecked()
  })

  test('E2E-MEMBER-005: should save role assignment', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId(`team-members-btn-roles-${TARGET_USER_ID}`).click()

    await authenticatedPage.getByTestId(`team-members-dlg-roles-chk-role-${TARGET_ROLE_ID}`).check()
    await authenticatedPage.getByTestId('team-members-dlg-roles-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-members-dlg-roles')).not.toBeVisible()
  })
})
