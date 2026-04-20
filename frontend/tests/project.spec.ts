import { test, expect } from './fixtures/auth'

test.describe('Project List', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/teams/1')
    await page.getByTestId('team-detail-tab-projects').click()
  })

  test('E2E-PROJ-001: Display project list with name, description, status', async ({
    authenticatedPage: page,
  }) => {
    const table = page.getByTestId('project-list-tbl-projects')
    await expect(table).toBeVisible()

    const rows = table.locator('tbody tr')
    await expect(rows.first()).toBeVisible()

    const firstRow = rows.first()
    await expect(firstRow.locator('td').nth(0)).not.toBeEmpty()
    await expect(firstRow.locator('td').nth(1)).toBeVisible()
    await expect(firstRow.locator('td').nth(2)).toBeVisible()
  })

  test('E2E-PROJ-002: Filter by status (archived)', async ({
    authenticatedPage: page,
  }) => {
    const statusSelect = page.getByTestId('project-list-sel-status')
    await statusSelect.click()
    await page.getByText('已归档').click()

    const table = page.getByTestId('project-list-tbl-projects')
    const rows = table.locator('tbody tr')
    const count = await rows.count()

    for (let i = 0; i < count; i++) {
      await expect(rows.nth(i).locator('td').nth(2)).toContainText('已归档')
    }
  })

  test('E2E-PROJ-003: Create new project via dialog', async ({
    authenticatedPage: page,
  }) => {
    await page.getByTestId('project-list-btn-create').click()

    const dialog = page.getByTestId('project-list-dlg-create')
    await expect(dialog).toBeVisible()

    const projectName = `E2E Project ${Date.now()}`
    await dialog.getByTestId('project-list-dlg-create-inp-name').fill(projectName)
    await dialog.getByTestId('project-list-dlg-create-txtarea-desc').fill('E2E test project description')
    await dialog.getByTestId('project-list-dlg-create-inp-start-date').fill('2026-01-01')

    await dialog.getByTestId('project-list-dlg-create-btn-submit').click()
    await expect(dialog).not.toBeVisible()

    const table = page.getByTestId('project-list-tbl-projects')
    await expect(table.locator('tbody')).toContainText(projectName)
  })

  test('Click project to view detail', async ({ authenticatedPage: page }) => {
    const table = page.getByTestId('project-list-tbl-projects')
    const firstProjectName = table.locator('tbody tr').first().locator('td').nth(0)
    await firstProjectName.click()

    await expect(page).toHaveURL(/\/projects\/\d+/)
    await expect(page.getByTestId('project-detail-txt-name')).toBeVisible()
  })
})

test.describe('Project Detail', () => {
  let projectId: string

  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/teams/1')
    await page.getByTestId('team-detail-tab-projects').click()

    const table = page.getByTestId('project-list-tbl-projects')
    await table.locator('tbody tr').first().locator('td').nth(0).click()

    const url = page.url()
    const match = url.match(/\/projects\/(\d+)/)
    projectId = match![1]
  })

  test('E2E-PROJ-004: Display project info and statistics', async ({
    authenticatedPage: page,
  }) => {
    await expect(page.getByTestId('project-detail-txt-name')).not.toBeEmpty()
    await expect(page.getByTestId('project-detail-txt-desc')).toBeVisible()
    await expect(page.getByTestId('project-detail-txt-start-date')).toBeVisible()
    await expect(page.getByTestId('project-detail-txt-status')).toBeVisible()

    await expect(page.getByTestId('project-detail-txt-stat-req')).toBeVisible()
    await expect(page.getByTestId('project-detail-txt-stat-task')).toBeVisible()
    await expect(page.getByTestId('project-detail-txt-stat-test')).toBeVisible()
  })

  test('E2E-PROJ-005: Edit project', async ({ authenticatedPage: page }) => {
    await page.getByTestId('project-detail-btn-edit').click()

    const dialog = page.getByTestId('project-detail-dlg-edit')
    await expect(dialog).toBeVisible()

    const nameInput = dialog.getByTestId('project-detail-dlg-edit-inp-name')
    await nameInput.clear()
    await nameInput.fill(`Updated Project ${Date.now()}`)

    await dialog.getByTestId('project-detail-dlg-edit-btn-save').click()
    await expect(dialog).not.toBeVisible()

    await expect(page.getByTestId('project-detail-txt-name')).not.toBeEmpty()
  })

  test('E2E-PROJ-006: Archive project', async ({ authenticatedPage: page }) => {
    await page.getByTestId('project-detail-btn-archive').click()

    const confirmDialog = page.getByTestId('project-detail-dlg-confirm-archive')
    if (await confirmDialog.isVisible()) {
      await confirmDialog.getByTestId('project-detail-dlg-confirm-archive-btn-confirm').click()
    }

    await expect(page.getByTestId('project-detail-txt-status')).toContainText('已归档')
  })

  test('E2E-PROJ-007: View iteration list from project detail', async ({
    authenticatedPage: page,
  }) => {
    await page.getByTestId('project-detail-tab-iterations').click()

    const iterationTable = page.getByTestId('iteration-list-tbl-iterations')
    await expect(iterationTable).toBeVisible()
  })

  test('Delete project when no active iterations', async ({ authenticatedPage: page }) => {
    await page.getByTestId('project-detail-btn-delete').click()

    const confirmDialog = page.getByTestId('project-detail-dlg-confirm-delete')
    if (await confirmDialog.isVisible()) {
      await confirmDialog.getByTestId('project-detail-dlg-confirm-delete-btn-confirm').click()
    }

    await expect(page).toHaveURL(/\/teams\/\d+/)

    const table = page.getByTestId('project-list-tbl-projects')
    if (await table.isVisible()) {
      await expect(table.locator('tbody')).not.toContainText(projectId)
    }
  })
})
