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
  const body = await resp.json()
  return body
}

async function createIteration(page: import('@playwright/test').Page) {
  const resp = await page.request.post('/api/v1/iterations', {
    data: {
      name: `迭代_${Date.now()}`,
      start_date: '2026-01-01',
      end_date: '2026-03-31',
    },
  })
  const body = await resp.json()
  return body
}

async function createReviewer(page: import('@playwright/test').Page) {
  const email = `reviewer_${Date.now()}@test.com`
  const resp = await page.request.post('/api/v1/auth/register', {
    data: { email, password: 'Test1234!', nickname: `reviewer_${Date.now()}` },
  })
  const body = await resp.json()
  return body
}

test.describe('需求详情页', () => {
  test.describe('查看需求基本信息 - E2E-REQ-001', () => {
    test('显示需求标题、类型标签、优先级、描述', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-txt-title')).toHaveText(req.title)
      await expect(authenticatedPage.getByTestId('req-detail-tag-type')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-priority')).toHaveText(/high|中|低/)
      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-req')).toHaveClass(/active|current/)
    })

    test('Bug 类型显示复现步骤、环境、严重程度', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage, {
        type: 'bug',
        type_detail: {
          reproduce_steps: '1. 打开页面 2. 点击按钮',
          environment: 'Chrome 120 / macOS',
          severity: 'critical',
        },
      })
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-txt-reproduce-steps')).toContainText('打开页面')
      await expect(authenticatedPage.getByTestId('req-detail-txt-environment')).toContainText('Chrome')
      await expect(authenticatedPage.getByTestId('req-detail-txt-severity')).toContainText('critical')
    })

    test('优化类型显示优化详情', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage, {
        type: 'optimization',
        type_detail: {
          current_issue: '当前性能差',
          expected_improvement: '提升至 200ms 以内',
          metrics: '响应时间',
        },
      })
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-txt-optimization-issue')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-txt-optimization-expected')).toBeVisible()
    })

    test('显示需求状态描述', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-txt-description')).toHaveText(req.description)
    })

    test('步骤条高亮当前状态', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-req')).toHaveClass(/active|current/)
    })
  })

  test.describe('编辑需求 - E2E-REQ-002', () => {
    test('drafting_req 状态下编辑需求标题和描述', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-edit-req').click()

      await authenticatedPage.getByTestId('req-detail-inp-title').fill('更新后的需求标题')
      await authenticatedPage.getByTestId('req-detail-txtarea-description').fill('更新后的描述')

      await authenticatedPage.getByTestId('req-detail-btn-save-req').click()

      await expect(authenticatedPage.getByTestId('req-detail-txt-title')).toHaveText('更新后的需求标题')
      await expect(authenticatedPage.getByTestId('req-detail-txt-description')).toHaveText('更新后的描述')
    })
  })

  test.describe('删除需求 - E2E-REQ-003', () => {
    test('drafting_req 状态下删除需求并跳转回看板', async ({ authenticatedPage }) => {
      const iteration = await createIteration(authenticatedPage)
      const req = await createRequirement(authenticatedPage, { iteration_id: iteration.id })
      await authenticatedPage.goto(`/requirements/${req.id}`)

      authenticatedPage.on('dialog', (dialog) => dialog.accept())
      await authenticatedPage.getByTestId('req-detail-btn-delete-req').click()

      await expect(authenticatedPage).toHaveURL(/\/(iterations|board)/)
    })
  })

  test.describe('提交需求审核 - E2E-REQ-004', () => {
    test('提交需求审核并选择审核人', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-submit-req-review').click()

      await expect(authenticatedPage.getByTestId('req-detail-dlg-submit-review')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-dlg-submit-review-sel-reviewer').click()
      await authenticatedPage.getByText(reviewer.nickname || reviewer.email).click()

      await authenticatedPage.getByTestId('req-detail-dlg-submit-review-btn-confirm').click()

      await expect(authenticatedPage.getByTestId('req-detail-txt-review-status')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-req')).toHaveClass(/review/)
    })
  })

  test.describe('审核通过需求 - E2E-REQ-005', () => {
    test('审核人点击通过后步骤条进入编写规范步骤', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: reviewer.id },
      })

      const loginResp = await authenticatedPage.request.post('/api/v1/auth/login', {
        data: { email: reviewer.email, password: 'Test1234!' },
      })
      const { access_token } = await loginResp.json()
      await authenticatedPage.evaluate((t) => localStorage.setItem('token', t), access_token)

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-approve').click()

      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-spec')).toHaveClass(/active|current/)
    })
  })

  test.describe('审核驳回需求 - E2E-REQ-006', () => {
    test('审核人驳回后步骤条退回编写需求步骤', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: reviewer.id },
      })

      const loginResp = await authenticatedPage.request.post('/api/v1/auth/login', {
        data: { email: reviewer.email, password: 'Test1234!' },
      })
      const { access_token } = await loginResp.json()
      await authenticatedPage.evaluate((t) => localStorage.setItem('token', t), access_token)

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-reject').click()
      await expect(authenticatedPage.getByTestId('req-detail-dlg-reject')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-dlg-reject-txtarea-comment').fill('需求描述不够清晰，请补充')
      await authenticatedPage.getByTestId('req-detail-dlg-reject-btn-confirm').click()

      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-req')).toHaveClass(/active|current|draft/)
      await expect(authenticatedPage.getByTestId('req-detail-txt-reject-reason')).toContainText('不够清晰')
    })

    test('显示审核历史', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: reviewer.id },
      })

      const loginResp = await authenticatedPage.request.post('/api/v1/auth/login', {
        data: { email: reviewer.email, password: 'Test1234!' },
      })
      const { access_token } = await loginResp.json()
      await authenticatedPage.evaluate((t) => localStorage.setItem('token', t), access_token)

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-btn-reject').click()
      await authenticatedPage.getByTestId('req-detail-dlg-reject-txtarea-comment').fill('驳回理由')
      await authenticatedPage.getByTestId('req-detail-dlg-reject-btn-confirm').click()

      await expect(authenticatedPage.getByTestId('req-detail-list-review-history')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-list-review-history').getByText('驳回')).toBeVisible()
    })
  })

  test.describe('状态徽标反映当前状态', () => {
    test('drafting_req 状态显示草稿徽标', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-tag-status')).toContainText(/drafting|草稿/)
    })
  })

  test.describe('编写规范文档 - E2E-REQ-007', () => {
    test('drafting_spec 状态下编辑并保存规范', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: (await createReviewer(authenticatedPage)).id },
      })
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/approve`)

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-tab-spec').click()

      await authenticatedPage.getByTestId('req-detail-txtarea-spec-content').fill(`# 规范文档

## 实体定义
User: { id, name, email }

## 表设计
users: id, name, email, created_at

## 页面结构
登录页 → 首页

## API 设计
POST /api/login

## 约束
- 邮箱唯一`)

      await authenticatedPage.getByTestId('req-detail-btn-save-spec').click()

      await expect(authenticatedPage.getByText(/保存成功/)).toBeVisible()
    })
  })

  test.describe('提交规范审核 - E2E-REQ-008', () => {
    test('提交规范审核并选择审核人', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: reviewer.id },
      })
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/approve`)
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/spec`, {
        data: { content: '# 规范内容' },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-tab-spec').click()
      await authenticatedPage.getByTestId('req-detail-btn-submit-spec-review').click()

      const specReviewer = await createReviewer(authenticatedPage)
      await authenticatedPage.getByTestId('req-detail-dlg-submit-spec-review-sel-reviewer').click()
      await authenticatedPage.getByText(specReviewer.nickname || specReviewer.email).click()
      await authenticatedPage.getByTestId('req-detail-dlg-submit-spec-review-btn-confirm').click()

      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-spec')).toHaveClass(/review/)
    })
  })

  test.describe('查看规范版本历史 - E2E-REQ-009', () => {
    test('查看多个版本并切换', async ({ authenticatedPage }) => {
      const reviewer = await createReviewer(authenticatedPage)
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/submit-review`, {
        data: { reviewer_id: reviewer.id },
      })
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/approve`)
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/spec`, {
        data: { content: '# 版本1' },
      })
      await authenticatedPage.request.post(`/api/v1/requirements/${req.id}/spec`, {
        data: { content: '# 版本2' },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)
      await authenticatedPage.getByTestId('req-detail-tab-spec-versions').click()

      await expect(authenticatedPage.getByTestId('req-detail-list-spec-versions')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-list-spec-versions').getByText('v2')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-list-spec-versions').getByText('v1')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-btn-spec-version-1').click()
      await expect(authenticatedPage.getByTestId('req-detail-txt-spec-version-content')).toContainText('版本1')

      await authenticatedPage.getByTestId('req-detail-btn-spec-version-2').click()
      await expect(authenticatedPage.getByTestId('req-detail-txt-spec-version-content')).toContainText('版本2')
    })
  })

  test.describe('审核通过后查看已通过状态 - E2E-REQ-014', () => {
    test('三步审核全部通过后步骤条显示已通过', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/requirements/${req.id}`, {
        data: { status: 'approved' },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await expect(authenticatedPage.getByTestId('req-detail-step-nav-step-approved')).toHaveClass(/complete|done|active/)
    })
  })

  test.describe('已通过状态下创建任务 - E2E-REQ-015', () => {
    test('创建任务并显示在任务列表中', async ({ authenticatedPage }) => {
      const req = await createRequirement(authenticatedPage)
      const assignee = await createReviewer(authenticatedPage)

      await authenticatedPage.request.patch(`/api/v1/requirements/${req.id}`, {
        data: { status: 'approved' },
      })

      await authenticatedPage.goto(`/requirements/${req.id}`)

      await authenticatedPage.getByTestId('req-detail-tab-tasks').click()
      await authenticatedPage.getByTestId('req-detail-btn-add-task').click()

      await expect(authenticatedPage.getByTestId('req-detail-dlg-add-task')).toBeVisible()

      await authenticatedPage.getByTestId('req-detail-dlg-add-task-inp-title').fill('实现用户 API')
      await authenticatedPage.getByTestId('req-detail-dlg-add-task-txtarea-desc').fill('实现用户相关 API 接口')
      await authenticatedPage.getByTestId('req-detail-dlg-add-task-sel-assignee').click()
      await authenticatedPage.getByText(assignee.nickname || assignee.email).click()

      await authenticatedPage.getByTestId('req-detail-dlg-add-task-btn-submit').click()

      await expect(authenticatedPage.getByTestId('req-detail-tbl-tasks')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-tasks').getByText('实现用户 API')).toBeVisible()
      await expect(authenticatedPage.getByTestId('req-detail-tbl-tasks').getByText(/pending|未开始/)).toBeVisible()
    })
  })
})
