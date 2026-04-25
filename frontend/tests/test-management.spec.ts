import { test, expect } from './fixtures/auth'

async function registerWithRetry(page: import('@playwright/test').Page, email: string, password: string, nickname: string) {
  for (let i = 0; i < 3; i++) {
    const resp = await page.request.post('/api/v1/auth/register', {
      data: { email, password, nickname },
    })
    const body = await resp.json()
    if (body.code === 0 || body.code === 40901) return body
    if (i === 2) return body
    await new Promise((r) => setTimeout(r, 500))
  }
}

async function createRequirement(page: import('@playwright/test').Page, overrides: Record<string, unknown> = {}) {
  const payload = {
    title: '测试需求标题',
    type: 'feature',
    priority: 'high',
    description: '测试需求描述内容',
    ...overrides,
  }
  const resp = await page.request.post('/api/v1/requirements', { data: payload })
  const body = await resp.json()
  return body.data || body
}

async function createReviewer(page: import('@playwright/test').Page) {
  const email = `reviewer_${Date.now()}@test.com`
  const body = await registerWithRetry(page, email, 'Test1234!', `reviewer_${Date.now()}`)
  if (!body.data) {
    throw new Error(`Register failed: ${JSON.stringify(body)}`)
  }
  return body.data
}

async function setupRequirementWithTests(page: import('@playwright/test').Page) {
  const reviewer = await createReviewer(page)
  const req = await createRequirement(page)

  await page.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
    data: { reviewer_id: reviewer.id },
  })

  const loginResp = await page.request.post('/api/v1/auth/login', {
    data: { email: reviewer.email, password: 'Test1234!' },
  })
  const loginData = await loginResp.json()
  if (!loginData.data || !loginData.data.token) {
    throw new Error(`Login failed for reviewer: ${JSON.stringify(loginData)}`)
  }
  const token = loginData.data.token
  await page.evaluate((t) => localStorage.setItem('token', t), token)
  await page.request.post(`/api/v1/requirements/${req.id}/approve`)

  const specReviewer = await createReviewer(page)
  await page.request.post(`/api/v1/requirements/${req.id}/spec`, {
    data: { content: '# 规范内容' },
  })
  await page.request.post(`/api/v1/requirements/${req.id}/submit-spec-review`, {
    data: { reviewer_id: specReviewer.id },
  })

  const specLogin = await page.request.post('/api/v1/auth/login', {
    data: { email: specReviewer.email, password: 'Test1234!' },
  })
  const specTokenBody = await specLogin.json()
  if (!specTokenBody.data || !specTokenBody.data.token) {
    throw new Error(`Login failed for specReviewer: ${JSON.stringify(specTokenBody)}`)
  }
  await page.evaluate((t) => localStorage.setItem('token', t), specTokenBody.data.token)
  await page.request.post(`/api/v1/requirements/${req.id}/approve-spec`)

  await page.request.patch(`/api/v1/requirements/${req.id}`, {
    data: { status: 'drafting_tests' },
  })

  return { req, reviewer }
}

test.describe('测试用例管理', () => {
  test.describe('显示测试用例列表', () => {
    test('需求详情页显示已有测试用例', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '已有用例',
          case_type: 'api',
          precondition: '前置条件',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('已有用例')).toBeVisible()
    })
  })

  test.describe('创建测试用例 - E2E-REQ-010', () => {
    test('创建 API 类型测试用例', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-add-test-case').click()

      await expect(authenticatedPage.getByTestId('req-detail-dlg-test-case')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-inp-title').fill('登录接口测试')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-sel-type').selectOption('api')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-precondition').fill('用户已注册')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-steps').fill('1. 发送 POST /api/login 2. 检查返回')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-expected').fill('返回 200 和 token')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-inp-related-api').fill('POST /api/login')

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-btn-save').click()

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('登录接口测试')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText(/TC-\d+|API/)).toBeVisible()
    })

    test('创建 E2E 类型测试用例', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-add-test-case').click()

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-inp-title').fill('登录流程端到端测试')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-sel-type').selectOption('e2e')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-precondition').fill('浏览器已打开')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-steps').fill('1. 打开登录页 2. 输入账号密码 3. 点击登录')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-expected').fill('跳转到首页')

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-btn-save').click()

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('登录流程端到端测试')).toBeVisible()
    })
  })

  test.describe('自动生成用例编号', () => {
    test('新创建的用例自动生成编号', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-add-test-case').click()

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-inp-title').fill('编号测试用例')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-sel-type').selectOption('api')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-precondition').fill('前置')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-steps').fill('步骤')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-expected').fill('预期')

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-btn-save').click()

      await expect(
        authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText(/^TC-\d+(-\d+)?$/)
      ).toBeVisible()
    })
  })

  test.describe('编辑测试用例 - E2E-REQ-011', () => {
    test('编辑已有测试用例内容', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '待编辑用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })
      const tc = await tcResp.json()

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId(`req-detail-btn-edit-test-case-${tc.id}`).click()

      await expect(authenticatedPage.getByTestId('req-detail-dlg-test-case')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-inp-title').fill('编辑后的用例标题')
      await authenticatedPage.getByTestId('req-detail-dlg-test-case-txtarea-expected').fill('更新后的预期结果')

      await authenticatedPage.getByTestId('req-detail-dlg-test-case-btn-save').click()

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('编辑后的用例标题')).toBeVisible()
    })
  })

  test.describe('删除测试用例 - E2E-REQ-012', () => {
    test('删除测试用例后从列表消失', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '待删除用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })
      const tc = await tcResp.json()

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('待删除用例')).toBeVisible()

      authenticatedPage.on('dialog', (dialog) => dialog.accept())
      await authenticatedPage.getByTestId(`req-detail-btn-delete-test-case-${tc.id}`).click()

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('待删除用例')).not.toBeVisible()
    })
  })

  test.describe('按类型筛选 - Filter by case_type', () => {
    test('筛选 API 类型用例', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: 'API用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })
      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: 'E2E用例',
          case_type: 'e2e',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-sel-filter-case-type').selectOption('api')

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('API用例')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('E2E用例')).not.toBeVisible()
    })

    test('筛选 E2E 类型用例', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: 'API用例2',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })
      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: 'E2E用例2',
          case_type: 'e2e',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-sel-filter-case-type').selectOption('e2e')

      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('E2E用例2')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-test-cases').getByText('API用例2')).not.toBeVisible()
    })
  })

  test.describe('提交测试用例审核 - E2E-REQ-013', () => {
    test('提交测试用例审核并选择审核人', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      await authenticatedPage.request.post('/api/v1/test-cases', {
        data: {
          title: '待审核用例',
          case_type: 'api',
          precondition: '前置',
          steps: '步骤',
          expected: '预期',
          requirement_id: req.id,
        },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-submit-tests-review').click()

      const testReviewer = await createReviewer(authenticatedPage)
      await authenticatedPage.getByTestId('req-detail-dlg-submit-tests-review-sel-reviewer').click()
      await authenticatedPage.getByText(testReviewer.nickname || testReviewer.email).click()
      await authenticatedPage.getByTestId('req-detail-dlg-submit-tests-review-btn-confirm').click()

      await expect(authenticatedPage.getByTestId('req-detail-step-nav')).toContainText(/test.*review|审核/i)
    })
  })
})

test.describe('测试执行', () => {
  async function createTaskWithRecords(page: import('@playwright/test').Page) {
    const { req } = await setupRequirementWithTests(page)

    const tcResp = await page.request.post('/api/v1/test-cases', {
      data: {
        title: '执行测试用例',
        case_type: 'api',
        precondition: '前置',
        steps: '步骤',
        expected: '预期',
        requirement_id: req.id,
      },
    })
    const tc = await tcResp.json()

    const assigneeEmail = `assignee_${Date.now()}@test.com`
    await registerWithRetry(page, assigneeEmail, 'Test1234!', `assignee_${Date.now()}`)
    const assigneeLogin = await page.request.post('/api/v1/auth/login', {
      data: { email: assigneeEmail, password: 'Test1234!' },
    })
    const assigneeBody = await assigneeLogin.json()
    const assignee = assigneeBody.data.user

    const taskResp = await page.request.post('/api/v1/tasks', {
      data: {
        title: '执行测试任务',
        description: '任务描述',
        requirement_id: req.id,
        assignee_id: assignee.id,
      },
    })
    const task = await taskResp.json()

    await page.request.patch(`/api/v1/tasks/${task.id}`, {
      data: { status: 'testing' },
    })

    const recordResp = await page.request.post(`/api/v1/tasks/${task.id}/test-records`, {
      data: { test_case_id: tc.id },
    })
    const record = await recordResp.json()

    return { task, tc, record, req }
  }

  test.describe('查看执行轮次', () => {
    test('显示测试执行轮次列表', async ({ authenticatedPage }) => {
      const { task } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await expect(authenticatedPage.getByTestId('task-detail-list-exec-rounds')).toBeVisible()
      await expect(authenticatedPage.getByTestId('task-detail-list-exec-rounds').getByText(/轮|round/i)).toBeVisible()
    })
  })

  test.describe('查看每轮记录', () => {
    test('展开轮次查看所有测试记录', async ({ authenticatedPage }) => {
      const { task, record } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-exec-round-${record.round_id || 1}`).click()

      await expect(authenticatedPage.getByTestId('task-detail-tbl-round-records')).toBeVisible()
      await expect(
        authenticatedPage.getByTestId('task-detail-tbl-round-records').getByTestId(`task-detail-row-record-${record.id}`)
      ).toBeVisible()
    })
  })

  test.describe('更新记录状态 - 通过', () => {
    test('将待执行记录更新为通过', async ({ authenticatedPage }) => {
      const { task, record } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '通过' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('执行通过')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByTestId(`task-detail-txt-record-status-${record.id}`)).toContainText(/pass|通过/)
    })
  })

  test.describe('更新记录状态 - 失败', () => {
    test('将待执行记录更新为失败并填写原因', async ({ authenticatedPage }) => {
      const { task, record } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '失败' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('执行失败')
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-reason').fill('超时')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByTestId(`task-detail-txt-record-status-${record.id}`)).toContainText(/fail|失败/)
    })
  })

  test.describe('更新记录状态 - 跳过', () => {
    test('将待执行记录更新为跳过', async ({ authenticatedPage }) => {
      const { task, record } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '跳过' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('环境不支持跳过')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByTestId(`task-detail-txt-record-status-${record.id}`)).toContainText(/skip|跳过/)
    })
  })

  test.describe('失败状态必填原因', () => {
    test('选择失败不填原因时无法保存', async ({ authenticatedPage }) => {
      const { task, record } = await createTaskWithRecords(authenticatedPage)

      await authenticatedPage.goto(`/tasks/${task.id}`)

      await authenticatedPage.getByTestId(`task-detail-btn-record-${record.id}`).click()

      await authenticatedPage.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '失败' })
      await authenticatedPage.getByTestId('task-detail-dlg-record-txtarea-result').fill('失败结果')

      await authenticatedPage.getByTestId('task-detail-dlg-record-btn-save').click()

      await expect(authenticatedPage.getByText(/失败原因必填|reason.*required/i)).toBeVisible()
    })
  })

  test.describe('查看测试统计 - E2E-REQ-016', () => {
    test('显示用例总数、通过数、失败数、跳过数、通过率', async ({ authenticatedPage }) => {
      const { req } = await setupRequirementWithTests(authenticatedPage)

      for (const [i, status] of ['pass', 'fail', 'skip', 'pass'].entries()) {
        const tcResp = await authenticatedPage.request.post('/api/v1/test-cases', {
          data: {
            title: `统计用例${i}`,
            case_type: 'api',
            precondition: '前置',
            steps: '步骤',
            expected: '预期',
            requirement_id: req.id,
          },
        })
        const tc = await tcResp.json()

        const assigneeEmail = `stats_assignee_${Date.now()}_${i}@test.com`
        await authenticatedPage.request.post('/api/v1/auth/register', {
          data: { email: assigneeEmail, password: 'Test1234!', nickname: `stats_assignee_${i}` },
        })

        const taskResp = await authenticatedPage.request.post('/api/v1/tasks', {
          data: {
            title: `统计任务${i}`,
            description: '描述',
            requirement_id: req.id,
            assignee_id: `stats_assignee_${i}`,
          },
        })
        const task = await taskResp.json()

        await authenticatedPage.request.patch(`/api/v1/tasks/${task.id}`, {
          data: { status: 'testing' },
        })

        await authenticatedPage.request.post(`/api/v1/tasks/${task.id}/test-records`, {
          data: {
            test_case_id: tc.id,
            status,
            actual_result: `结果${i}`,
            ...(status === 'fail' ? { failure_reason: '原因' } : {}),
          },
        })
      }

      await authenticatedPage.goto(`/requirements/${req.id}`)
      await authenticatedPage.getByTestId('req-detail-tab-test-stats').click()

      await expect(authenticatedPage.getByTestId('req-detail-txt-test-stats')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-test-stats')).toContainText(/通过率|pass rate/i)
      await expect(authenticatedPage.getByTestId('req-detail-txt-test-total-count')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-test-pass-count')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-test-fail-count')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-test-skip-count')).toBeVisible()
    })
  })
})
