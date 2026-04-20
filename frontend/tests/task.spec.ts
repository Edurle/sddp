import { test, expect } from './fixtures/auth'

async function createRequirement(page: import('@playwright/test').Page, overrides: Record<string, unknown> = {}) {
  const payload = {
    title: '测试需求标题',
    type: 'feature',
    priority: 'high',
    description: '测试需求描述内容',
    ...overrides,
  }
  const resp = await page.request.post('/api/v1/requirements', { data: payload })
  return resp.json()
}

async function createApprovedRequirement(page: import('@playwright/test').Page) {
  const email = `reviewer_${Date.now()}@test.com`
  const reviewerResp = await page.request.post('/api/v1/auth/register', {
    data: { email, password: 'Test1234!', nickname: `reviewer_${Date.now()}` },
  })
  const reviewer = await reviewerResp.json()

  const req = await createRequirement(page)
  await page.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
    data: { reviewer_id: reviewer.id },
  })

  const loginResp = await page.request.post('/api/v1/auth/login', {
    data: { email, password: 'Test1234!' },
  })
  const { access_token } = await loginResp.json()
  await page.evaluate((t) => localStorage.setItem('token', t), access_token)
  await page.request.post(`/api/v1/requirements/${req.id}/approve`)

  return { req, reviewerToken: access_token }
}

async function createTask(page: import('@playwright/test').Page, overrides: Record<string, unknown> = {}) {
  const { req } = await createApprovedRequirement(page)
  const assigneeEmail = `assignee_${Date.now()}@test.com`
  await page.request.post('/api/v1/auth/register', {
    data: { email: assigneeEmail, password: 'Test1234!', nickname: `assignee_${Date.now()}` },
  })
  const assigneeLogin = await page.request.post('/api/v1/auth/login', {
    data: { email: assigneeEmail, password: 'Test1234!' },
  })
  const assignee = await assigneeLogin.json()

  const payload = {
    title: '测试任务标题',
    description: '测试任务描述',
    requirement_id: req.id,
    assignee_id: assignee.id || assignee.user_id,
    ...overrides,
  }
  const resp = await page.request.post('/api/v1/tasks', { data: payload })
  const task = await resp.json()
  return { task, req, assignee }
}

test.describe('任务详情页', () => {
  test.describe('查看任务详情 - E2E-TASK-001', () => {
    test('pending 状态显示任务信息和操作按钮', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-txt-status')).toContainText(/pending|未开始/)
      await expect(authenticatedPage.getByTestId('task-detail-btn-start')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-btn-edit')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-btn-delete')).toBeVisible()
    })

    test('显示任务标题和描述', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-txt-title')).toHaveText(task.title)
      await expect(authenticatedPage.getByTestId('task-detail-txt-description')).toHaveText(task.description)
    })

    test('显示指派人信息', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-txt-assignee')).toBeVisible()
    })

    test('显示关联需求信息', async ({ authenticatedPage }) => {
      const { task, req } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-txt-linked-requirement')).toContainText(req.title)
    })
  })

  test.describe('编辑任务 - E2E-TASK-002', () => {
    test('pending 状态下编辑任务标题和描述', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId('task-detail-btn-edit').click()

      await authenticatedPage.getByTestId('task-detail-inp-title').fill('更新后的任务标题')
      await authenticatedPage.getByTestId('task-detail-txtarea-description').fill('更新后的描述')

      await authenticatedPage.getByTestId('task-detail-btn-save').click()

      await expect(authenticatedPage.getByTestId('task-detail-txt-title')).toHaveText('更新后的任务标题')
      await expect(authenticatedPage.getByTestId('task-detail-txt-description')).toHaveText('更新后的描述')
    })
  })

  test.describe('查看规范文档 - E2E-TASK-003', () => {
    test('只读模式显示关联需求的规范文档', async ({ authenticatedPage }) => {
      const { task, req } = await createTask(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/spec`, {
        data: { content: '# 规范内容\n\n## API 设计\nPOST /api/users' },
      })

      await authenticatedPage.goto(`/tasks/${task.id}`)
      await authenticatedPage.getByTestId('task-detail-tab-spec').click()

      await expect(authenticatedPage.getByTestId('task-detail-txt-spec-content')).toContainText('规范内容')
    })
  })

  test.describe('开始编码 - E2E-TASK-004', () => {
    test('pending 状态点击开始编码后状态变为编码中', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)
      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId('task-detail-btn-start').click()

      await expect(authenticatedPage.getByTestId('task-detail-txt-status')).toContainText(/coding|编码中/)
    })
  })

  test.describe('开始测试 - E2E-TASK-005', () => {
    test('coding 状态点击开始测试后进入测试中', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'coding' },
      })

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId('task-detail-btn-start-testing').click()

      await expect(authenticatedPage.getByTestId('task-detail-txt-status')).toContainText(/testing|测试中/)
      await expect(authenticatedPage.getByTestId('task-detail-tab-test-exec')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-tbl-test-records')).toBeVisible()
    })
  })

  test.describe('填写测试执行结果 - 通过 - E2E-TASK-006', () => {
    test('将测试记录状态设为通过', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const testCase = {
        title: '测试用例1',
        case_type: 'api',
        precondition: '前置条件',
        steps: '操作步骤',
        expected: '预期结果',
      }
      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: { ...testCase, requirement_id: task.requirement_id },
      })
      const tc = await tcResp.json()

      const recordResp = await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
        data: { test_case_id: tc.id },
      })
      const record = await recordResp.json()

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()
      await expect(authenticatedPage.getByTestId('task-detail-dlg-record')).toBeVisible()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '通过' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('接口返回200，结果符合预期')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByTestId(`task-detail-txt-record-status-${record.id}`)).toContainText(/pass|通过/)
    })
  })

  test.describe('填写测试执行结果 - 失败 - E2E-TASK-007', () => {
    test('将测试记录状态设为失败并填写失败原因', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const testCase = {
        title: '测试用例-失败',
        case_type: 'api',
        precondition: '前置条件',
        steps: '操作步骤',
        expected: '预期结果',
      }
      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: { ...testCase, requirement_id: task.requirement_id },
      })
      const tc = await tcResp.json()

      const recordResp = await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
        data: { test_case_id: tc.id },
      })
      const record = await recordResp.json()

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '失败' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('返回 500 错误')
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-reason').fill('服务端空指针异常')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByTestId(`task-detail-txt-record-status-${record.id}`)).toContainText(/fail|失败/)
    })
  })

  test.describe('填写测试结果 - 失败未填原因 - E2E-TASK-008', () => {
    test('选择失败但不填原因时显示错误', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const testCase = {
        title: '测试用例-未填原因',
        case_type: 'e2e',
        precondition: '前置条件',
        steps: '操作步骤',
        expected: '预期结果',
      }
      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: { ...testCase, requirement_id: task.requirement_id },
      })
      const tc = await tcResp.json()

      const recordResp = await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
        data: { test_case_id: tc.id },
      })
      const record = await recordResp.json()

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '失败' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('结果不符')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByText(/失败原因必填|reason.*required/i)).toBeVisible()
    })
  })

  test.describe('完成任务 - 全部通过 - E2E-TASK-009', () => {
    test('所有测试通过后可完成任务', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '通过的用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: task.requirement_id,
        },
      })
      const tc = await tcResp.json()

      await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
        data: { test_case_id: tc.id, status: 'pass', actual_result: '符合预期' },
      })

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-txt-test-summary')).toContainText(/全部通过|all.*pass/i)

      await authenticatedPage.getByTestId('task-detail-btn-complete').click()

      await expect(authenticatedPage.getByTestId('task-detail-txt-status')).toContainText(/completed|已完成/)
    })
  })

  test.describe('完成任务 - 有失败用例 - E2E-TASK-010', () => {
    test('存在失败用例时无法完成任务', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '失败的用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: task.requirement_id,
        },
      })
      const tc = await tcResp.json()

      await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
        data: {
          test_case_id: tc.id,
          status: 'fail',
          actual_result: '返回500',
          failure_reason: '空指针',
        },
      })

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId('task-detail-btn-complete').click()

      await expect(authenticatedPage.getByText(/存在未通过的测试用例/)).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-txt-status')).toContainText(/testing|测试中/)
    })
  })

  test.describe('查看历史执行记录 - E2E-TASK-011', () => {
    test('查看多轮测试执行历史', async ({ authenticatedPage }) => {
      const { task } = await createTask(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
        data: { status: 'testing' },
      })

      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '历史用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: task.requirement_id,
        },
      })
      const tc = await tcResp.json()

      await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-rounds`, {
        data: { test_case_id: tc.id, status: 'fail', actual_result: '第一轮失败', failure_reason: '原因' },
      })
      const round2 = await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-rounds`, {
        data: { test_case_id: tc.id, status: 'pass', actual_result: '第二轮通过' },
      })
      const round2Body = await round2.json()

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-list-exec-history')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-list-exec-history').getByText('第 1 轮')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-list-exec-history').getByText('第 2 轮')).toBeVisible()

      await authenticatedPage.getByTestId(`task-detail-btn-exec-round-${round2Body.id || 2}`).click()

      await expect(authenticatedPage.getByTestId('task-detail-tbl-round-records')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-tbl-round-records').getByText('通过')).toBeVisible()
    })
  })
})
