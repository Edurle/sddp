import { test, expect } from './fixtures/auth'

test.describe('Iteration List', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')
    await page.getByTestId('project-detail-tab-iterations').click()
  })

  test('E2E-ITER-006: Display iteration list with name, dates, status', async ({
    authenticatedPage: page,
  }) => {
    const table = page.getByTestId('iteration-list-tbl-iterations')
    await expect(table).toBeVisible()

    const rows = table.locator('tbody tr')
    await expect(rows.first()).toBeVisible()

    const firstRow = rows.first()
    await expect(firstRow.locator('td').nth(0)).not.toBeEmpty()
    await expect(firstRow.locator('td').nth(1)).toBeVisible()
    await expect(firstRow.locator('td').nth(2)).toBeVisible()
    await expect(firstRow.locator('td').nth(3)).toBeVisible()
  })

  test('E2E-ITER-001: Create new iteration', async ({ authenticatedPage: page }) => {
    await page.getByTestId('iteration-list-btn-create').click()

    const dialog = page.getByTestId('iteration-list-dlg-create')
    await expect(dialog).toBeVisible()

    await dialog.getByTestId('iteration-list-dlg-create-inp-name').fill('Sprint 1')
    await dialog.getByTestId('iteration-list-dlg-create-txtarea-goal').fill('Complete first iteration goals')
    await dialog.getByTestId('iteration-list-dlg-create-inp-start-date').fill('2026-01-01')
    await dialog.getByTestId('iteration-list-dlg-create-inp-end-date').fill('2026-01-14')

    await dialog.getByTestId('iteration-list-dlg-create-btn-submit').click()
    await expect(dialog).not.toBeVisible()

    const table = page.getByTestId('iteration-list-tbl-iterations')
    await expect(table.locator('tbody')).toContainText('Sprint 1')
    await expect(table.locator('tbody')).toContainText('计划中')
  })

  test('E2E-ITER-006: Filter by status (in progress)', async ({ authenticatedPage: page }) => {
    const statusSelect = page.getByTestId('iteration-list-sel-status')
    await statusSelect.click()
    await page.getByText('进行中').click()

    const table = page.getByTestId('iteration-list-tbl-iterations')
    const rows = table.locator('tbody tr')
    const count = await rows.count()

    for (let i = 0; i < count; i++) {
      await expect(rows.nth(i).locator('td').nth(3)).toContainText('进行中')
    }
  })
})

test.describe('Iteration Detail & Actions', () => {
  let iterationId: string

  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')
    await page.getByTestId('project-detail-tab-iterations').click()

    const table = page.getByTestId('iteration-list-tbl-iterations')
    const firstRow = table.locator('tbody tr').first()
    const idCell = firstRow.locator('td').nth(0)
    iterationId = (await idCell.getAttribute('data-iteration-id')) || '1'
  })

  test('Display iteration info and statistics', async ({ authenticatedPage: page }) => {
    const row = page
      .getByTestId('iteration-list-tbl-iterations')
      .locator('tbody tr')
      .first()
    await expect(row).toBeVisible()

    await expect(row.locator('td').nth(0)).not.toBeEmpty()
    await expect(row.locator('td').nth(1)).toBeVisible()
    await expect(row.locator('td').nth(2)).toBeVisible()
    await expect(row.locator('td').nth(3)).toBeVisible()
  })

  test('E2E-ITER-002: Edit iteration — start_date is read-only', async ({
    authenticatedPage: page,
  }) => {
    await page.getByTestId(`iteration-list-btn-edit-${iterationId}`).click()

    const dialog = page.getByTestId('iteration-list-dlg-edit')
    await expect(dialog).toBeVisible()

    const startDateInput = dialog.getByTestId('iteration-list-dlg-edit-inp-start-date')
    await expect(startDateInput).toBeDisabled()

    const endDateInput = dialog.getByTestId('iteration-list-dlg-edit-inp-end-date')
    await endDateInput.clear()
    await endDateInput.fill('2026-02-01')

    await dialog.getByTestId('iteration-list-dlg-edit-btn-submit').click()
    await expect(dialog).not.toBeVisible()
  })

  test('E2E-ITER-003: Start iteration', async ({ authenticatedPage: page }) => {
    await page.getByTestId(`iteration-list-btn-start-${iterationId}`).click()

    const confirmDialog = page.getByTestId('iteration-list-dlg-confirm-start')
    if (await confirmDialog.isVisible()) {
      await confirmDialog.getByTestId('iteration-list-dlg-confirm-start-btn-confirm').click()
    }

    const row = page
      .getByTestId('iteration-list-tbl-iterations')
      .locator('tbody tr')
      .first()
    await expect(row.locator('td').nth(3)).toContainText('进行中')
  })

  test('E2E-ITER-004: Complete iteration — success', async ({ authenticatedPage: page }) => {
    await page.getByTestId(`iteration-list-btn-complete-${iterationId}`).click()

    const confirmDialog = page.getByTestId('iteration-list-dlg-confirm-complete')
    if (await confirmDialog.isVisible()) {
      await confirmDialog.getByTestId('iteration-list-dlg-confirm-complete-btn-confirm').click()
    }

    const row = page
      .getByTestId('iteration-list-tbl-iterations')
      .locator('tbody tr')
      .first()
    await expect(row.locator('td').nth(3)).toContainText('已完成')
  })

  test('E2E-ITER-005: Complete iteration — has uncompleted tasks', async ({
    authenticatedPage: page,
  }) => {
    await page.getByTestId(`iteration-list-btn-complete-${iterationId}`).click()

    const errorAlert = page.getByTestId('iteration-list-txt-complete-error')
    await expect(errorAlert).toBeVisible()
    await expect(errorAlert).not.toBeEmpty()
  })
})

test.describe('Kanban Board', () => {
  let iterationId: string

  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')
    await page.getByTestId('project-detail-tab-iterations').click()

    const table = page.getByTestId('iteration-list-tbl-iterations')
    const firstRow = table.locator('tbody tr').first()
    const idCell = firstRow.locator('td').nth(0)
    iterationId = (await idCell.getAttribute('data-iteration-id')) || '1'

    await page.getByTestId(`iteration-list-btn-kanban-${iterationId}`).click()
    await expect(page).toHaveURL(/\/iterations\/\d+\/kanban/)
  })

  test('E2E-KANBAN-001: Display kanban columns and requirement cards', async ({
    authenticatedPage: page,
  }) => {
    await expect(page.getByTestId('iteration-kanban-txt-name')).not.toBeEmpty()

    const columns = page.locator('[data-testid^="iteration-kanban-col-"]')
    const colCount = await columns.count()
    expect(colCount).toBeGreaterThanOrEqual(1)

    const cards = page.locator('[data-testid^="iteration-kanban-card-req-"]')
    const cardCount = await cards.count()
    if (cardCount > 0) {
      const firstCard = cards.first()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-title')).not.toBeEmpty()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-type')).toBeVisible()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-priority')).toBeVisible()
    }
  })

  test('E2E-KANBAN-002: Create requirement from kanban', async ({ authenticatedPage: page }) => {
    await page.getByTestId('iteration-kanban-btn-add-req').click()

    const dialog = page.getByTestId('iteration-kanban-dlg-create-req')
    await expect(dialog).toBeVisible()

    const reqTitle = `E2E Requirement ${Date.now()}`
    await dialog.getByTestId('iteration-kanban-dlg-create-req-inp-title').fill(reqTitle)
    await dialog.getByTestId('iteration-kanban-dlg-create-req-sel-type').selectOption({ label: '功能需求' })
    await dialog.getByTestId('iteration-kanban-dlg-create-req-inp-priority').fill('1')
    await dialog.getByTestId('iteration-kanban-dlg-create-req-txtarea-desc').fill('E2E test requirement description')
    await dialog.getByTestId('iteration-kanban-dlg-create-req-txtarea-type-detail').fill('Functional requirement details')

    await dialog.getByTestId('iteration-kanban-dlg-create-req-btn-submit').click()
    await expect(dialog).not.toBeVisible()

    const draftColumn = page.getByTestId('iteration-kanban-col-draft')
    if (await draftColumn.isVisible()) {
      await expect(draftColumn).toContainText(reqTitle)
    }
  })

  test('E2E-KANBAN-003: Click card to view requirement detail', async ({ authenticatedPage: page }) => {
    const cards = page.locator('[data-testid^="iteration-kanban-card-req-"]')
    const cardCount = await cards.count()

    if (cardCount > 0) {
      const firstCardId = await cards.first().getAttribute('data-testid')
      const reqId = firstCardId!.replace('iteration-kanban-card-req-', '')

      await page.getByTestId(`iteration-kanban-btn-req-${reqId}`).click()
      await expect(page).toHaveURL(/\/requirements\/\d+/)
    }
  })

  test('E2E-KANBAN-004: Display iteration statistics', async ({ authenticatedPage: page }) => {
    const statElement = page.getByTestId('iteration-kanban-txt-stat')
    await expect(statElement).toBeVisible()
    await expect(statElement).not.toBeEmpty()
  })
})
