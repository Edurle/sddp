import { test, expect } from './fixtures/auth'

test.describe('Iteration List', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')
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

test.describe.configure({ mode: 'serial' })

test.describe('Iteration Detail & Actions', () => {
  let iterationId: string

  function getIterationRow(page: import('@playwright/test').Page, id: string) {
    return page
      .getByTestId('iteration-list-tbl-iterations')
      .locator('tbody tr')
      .locator(`[data-iteration-id="${id}"]`)
      .locator('..')
  }

  test('setup: create iteration via API', async ({ authenticatedPage: page }) => {
    const resp = await page.request.post('/api/v1/projects/1/iterations', {
      data: {
        name: `E2E Test Iter ${Date.now()}`,
        goal: 'E2E test iteration',
        start_date: '2026-01-01',
        end_date: '2026-12-31',
      },
    })
    const body = await resp.json()
    expect(body.code).toBe(0)
    iterationId = String(body.data.id)

    await page.goto('/projects/1')
    const row = page
      .getByTestId('iteration-list-tbl-iterations')
      .locator('tbody tr')
      .first()
    await expect(row).toBeVisible()
  })

  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')
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

    const row = getIterationRow(page, iterationId)
    await expect(row.locator('td').nth(3)).toContainText('进行中')
  })

  test('E2E-ITER-004: Complete iteration — success', async ({ authenticatedPage: page }) => {
    await page.getByTestId(`iteration-list-btn-complete-${iterationId}`).click()

    const confirmDialog = page.getByTestId('iteration-list-dlg-confirm-complete')
    if (await confirmDialog.isVisible()) {
      await confirmDialog.getByTestId('iteration-list-dlg-confirm-complete-btn-confirm').click()
    }

    const row = getIterationRow(page, iterationId)
    await expect(row.locator('td').nth(3)).toContainText('已完成')
  })

  test('E2E-ITER-005: Complete iteration — has uncompleted tasks', async ({
    authenticatedPage: page,
  }) => {
    const iterResp = await page.request.post('/api/v1/projects/1/iterations', {
      data: {
        name: `E2E Unblock Iter ${Date.now()}`,
        goal: 'E2E unblock test',
        start_date: '2026-01-01',
        end_date: '2026-12-31',
      },
    })
    const iterBody = await iterResp.json()
    const unblockId = String(iterBody.data.id)

    await page.request.post('/api/v1/requirements', {
      data: {
        title: 'Blocking Requirement',
        type: 'feature',
        priority: 'high',
        description: 'This req blocks completion',
        iteration_id: Number(unblockId),
      },
    })

    await page.goto('/projects/1')

    await page.getByTestId(`iteration-list-btn-start-${unblockId}`).click()
    const startConfirm = page.getByTestId('iteration-list-dlg-confirm-start')
    if (await startConfirm.isVisible()) {
      await startConfirm.getByTestId('iteration-list-dlg-confirm-start-btn-confirm').click()
    }

    await page.getByTestId(`iteration-list-btn-complete-${unblockId}`).click()

    const errorAlert = page.getByTestId('iteration-list-txt-complete-error')
    await expect(errorAlert).toBeVisible()
    await expect(errorAlert).not.toBeEmpty()
  })
})

test.describe('Kanban Board', () => {
  let iterationId: string

  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.goto('/projects/1')

    const table = page.getByTestId('iteration-list-tbl-iterations')
    const firstRow = table.locator('tbody tr').first()
    const idCell = firstRow.locator('td').nth(0)
    iterationId = (await idCell.getAttribute('data-iteration-id')) || '1'

    await page.getByTestId(`iteration-list-btn-kanban-${iterationId}`).click()
    await expect(page).toHaveURL(/\/iterations\/\d+\/kanban/)
  })

  test('E2E-KANBAN-001: Display card grid with status badges', async ({
    authenticatedPage: page,
  }) => {
    await expect(page.getByTestId('iteration-kanban-txt-name')).not.toBeEmpty()

    await expect(page.getByTestId('iteration-kanban-grid')).toBeVisible()

    const cards = page.locator('[data-testid^="iteration-kanban-card-req-"]')
    const cardCount = await cards.count()
    if (cardCount > 0) {
      const firstCard = cards.first()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-title')).not.toBeEmpty()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-type')).toBeVisible()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-priority')).toBeVisible()
      await expect(firstCard.getByTestId('iteration-kanban-card-req-badge-status')).toBeVisible()
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

    const grid = page.getByTestId('iteration-kanban-grid')
    await expect(grid).toContainText(reqTitle)

    const cards = grid.locator('[data-testid^="iteration-kanban-card-req-"]')
    const newCard = cards.filter({ hasText: reqTitle })
    await expect(newCard.getByTestId('iteration-kanban-card-req-badge-status')).toContainText('草稿')
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

  test('E2E-KANBAN-005: Filter cards by status', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('iteration-kanban-filter-all')).toBeVisible()
    await expect(page.getByTestId('iteration-kanban-filter-draft')).toBeVisible()

    await page.getByTestId('iteration-kanban-filter-draft').click()

    const cards = page.locator('[data-testid^="iteration-kanban-card-req-"]')
    const cardCount = await cards.count()
    for (let i = 0; i < cardCount; i++) {
      await expect(cards.nth(i).getByTestId('iteration-kanban-card-req-badge-status')).toContainText('草稿')
    }

    await page.getByTestId('iteration-kanban-filter-all').click()
    const allCards = page.locator('[data-testid^="iteration-kanban-card-req-"]')
    const allCount = await allCards.count()
    expect(allCount).toBeGreaterThanOrEqual(cardCount)
  })
})
