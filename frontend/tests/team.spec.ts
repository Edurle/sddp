import { test, expect } from './fixtures/auth'

const TEAM_ID = 'test-team-id'

test.describe('Team Detail Page', () => {
  test('E2E-TEAM-001: should display team name and owner info', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await expect(authenticatedPage.getByTestId('team-detail-txt-name')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-detail-txt-owner')).toBeVisible()
  })

  test('E2E-TEAM-001: should display team description', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await expect(authenticatedPage.getByTestId('team-detail-txt-desc')).toBeVisible()
  })

  test('E2E-TEAM-001: should display member count', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await expect(authenticatedPage.getByTestId('team-detail-txt-member-count')).toBeVisible()
  })

  test('E2E-TEAM-002: should switch to members tab', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await authenticatedPage.getByTestId('team-detail-tab-members').click()

    await expect(authenticatedPage.getByTestId('team-members-tbl-members')).toBeVisible()
  })

  test('E2E-TEAM-002: should switch to roles tab', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await authenticatedPage.getByTestId('team-detail-tab-roles').click()

    await expect(authenticatedPage.getByTestId('team-roles-tbl-roles')).toBeVisible()
  })

  test('E2E-TEAM-002: should switch to settings tab', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await authenticatedPage.getByTestId('team-detail-tab-settings').click()

    await expect(authenticatedPage.getByTestId('team-settings-inp-name')).toBeVisible()
  })

  test('E2E-TEAM-002: should switch to projects tab', async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)

    await authenticatedPage.getByTestId('team-detail-tab-projects').click()

    await expect(authenticatedPage.getByTestId('team-detail-projects-list')).toBeVisible()
  })
})

test.describe('Team Settings Tab', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.goto(`/teams/${TEAM_ID}`)
    await authenticatedPage.getByTestId('team-detail-tab-settings').click()
  })

  test('E2E-SET-001: should edit team name', async ({ authenticatedPage }) => {
    const nameInput = authenticatedPage.getByTestId('team-settings-inp-name')
    await nameInput.clear()
    await nameInput.fill('Updated Team Name')

    await authenticatedPage.getByTestId('team-settings-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-settings-txt-success')).toContainText('保存成功')
  })

  test('E2E-SET-001: should edit team description', async ({ authenticatedPage }) => {
    const descTextarea = authenticatedPage.getByTestId('team-settings-txtarea-desc')
    await descTextarea.clear()
    await descTextarea.fill('Updated team description')

    await authenticatedPage.getByTestId('team-settings-btn-save').click()

    await expect(authenticatedPage.getByTestId('team-settings-txt-success')).toContainText('保存成功')
  })

  test('E2E-SET-002: should transfer team ownership', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-settings-btn-transfer').click()

    await expect(authenticatedPage.getByTestId('team-settings-dlg-transfer')).toBeVisible()

    await authenticatedPage.getByTestId('team-settings-dlg-transfer-sel-owner').selectOption({ index: 1 })

    await authenticatedPage.getByTestId('team-settings-dlg-transfer-btn-confirm').click()

    await expect(authenticatedPage.getByTestId('team-detail-txt-owner')).not.toContainText('当前用户')
  })

  test('E2E-SET-002: should show transfer confirmation dialog', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-settings-btn-transfer').click()

    await expect(authenticatedPage.getByTestId('team-settings-dlg-transfer')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-settings-dlg-transfer-sel-owner')).toBeVisible()
    await expect(authenticatedPage.getByTestId('team-settings-dlg-transfer-btn-confirm')).toBeVisible()
  })

  test('E2E-SET-003: should dissolve team with confirmation', async ({ authenticatedPage }) => {
    await authenticatedPage.getByTestId('team-settings-btn-dissolve').click()

    await expect(authenticatedPage.getByTestId('team-settings-dlg-dissolve')).toBeVisible()

    await authenticatedPage.getByTestId('team-settings-dlg-dissolve-btn-confirm').click()

    await expect(authenticatedPage).toHaveURL(/\/dashboard|\/profile/)
  })

  test('non-owner cannot see dissolve button', async ({ authenticatedPage }) => {
    const dissolveBtn = authenticatedPage.getByTestId('team-settings-btn-dissolve')

    await expect(dissolveBtn).not.toBeVisible()
  })
})
