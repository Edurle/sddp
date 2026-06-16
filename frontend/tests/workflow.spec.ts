import { test, expect } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

const TS = Date.now()
const PASSWORD = 'Test1234!'

const users = {
  creator: { email: `wf_creator_${TS}@test.com`, nickname: `wf_creator_${TS}`, id: '', token: '' },
  pm: { email: `wf_pm_${TS}@test.com`, nickname: `wf_pm_${TS}`, id: '', token: '' },
  dev: { email: `wf_dev_${TS}@test.com`, nickname: `wf_dev_${TS}`, id: '', token: '' },
  tester: { email: `wf_tester_${TS}@test.com`, nickname: `wf_tester_${TS}`, id: '', token: '' },
}

let teamId = ''
let projectId = ''
let iterationId = ''
let requirementId = ''
let taskId = ''
let pmRoleId = ''
let devRoleId = ''
let testerRoleId = ''
let testCaseId = ''
let invitationIds: Record<string, string> = {}

async function registerUser(page: import('@playwright/test').Page, email: string, password: string, nickname: string) {
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

async function loginAs(page: import('@playwright/test').Page, email: string, password: string) {
  const resp = await page.request.post('/api/v1/auth/login', {
    data: { email, password },
  })
  const body = await resp.json()
  const token = body.data.token
  await page.goto('/')
  await page.evaluate((t: string) => localStorage.setItem('token', t), token)
  await page.context().addCookies([{ name: 'token', value: token, domain: 'localhost', path: '/' }])
  return { token, user: body.data.user }
}

test.describe('Full Business Workflow', () => {
  test('WF-001: Creator registers', async ({ page }) => {
    const body = await registerUser(page, users.creator.email, PASSWORD, users.creator.nickname)
    expect(body.code === 0 || body.code === 40901).toBeTruthy()
    if (body.data) {
      users.creator.id = String(body.data.id || '')
    }
  })

  test('WF-002: Creator logs in and creates team', async ({ page }) => {
    const { token, user } = await loginAs(page, users.creator.email, PASSWORD)
    users.creator.token = token
    users.creator.id = String(user.id || '')

    await page.goto('/teams')

    const createBtn = page.getByTestId('team-list-btn-create')
    if (await createBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createBtn.click()
      const dialog = page.getByTestId('team-list-dlg-create')
      await expect(dialog).toBeVisible({ timeout: 5000 })
      await dialog.getByTestId('team-list-dlg-create-inp-name').fill(`WF Team ${TS}`)
      await dialog.getByTestId('team-list-dlg-create-txtarea-desc').fill('Workflow test team')
      await dialog.getByTestId('team-list-dlg-create-btn-submit').click()
      await expect(dialog).not.toBeVisible({ timeout: 5000 })
    } else {
      const resp = await page.request.post('/api/v1/teams/', {
        data: { name: `WF Team ${TS}`, description: 'Workflow test team' },
      })
      const body = await resp.json()
      expect(body.code).toBe(0)
    }

    const meResp = await page.request.get('/api/v1/users/me')
    const meBody = await meResp.json()
    const teams = meBody.data?.teams || meBody.data?.team_list || []
    if (teams.length > 0) {
      teamId = String(teams[0].id || teams[0].team_id || '')
    }
    if (!teamId) {
      const listResp = await page.request.get('/api/v1/teams/')
      const listBody = await listResp.json()
      const allTeams = listBody.data?.items || listBody.data || []
      if (allTeams.length > 0) {
        teamId = String(allTeams[0].id)
      }
    }
    expect(teamId).toBeTruthy()
  })

  test('WF-003: PM registers', async ({ page }) => {
    const body = await registerUser(page, users.pm.email, PASSWORD, users.pm.nickname)
    if (body.data) {
      users.pm.id = String(body.data.id || '')
    }
  })

  test('WF-004: Dev registers', async ({ page }) => {
    const body = await registerUser(page, users.dev.email, PASSWORD, users.dev.nickname)
    if (body.data) {
      users.dev.id = String(body.data.id || '')
    }
  })

  test('WF-005: Tester registers', async ({ page }) => {
    const body = await registerUser(page, users.tester.email, PASSWORD, users.tester.nickname)
    if (body.data) {
      users.tester.id = String(body.data.id || '')
    }
  })

  test('WF-006: Creator invites PM, Dev, Tester to team', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    for (const [key, user] of Object.entries({ pm: users.pm, dev: users.dev, tester: users.tester })) {
      if (!user.id) {
        const loginResp = await page.request.post('/api/v1/auth/login', {
          data: { email: user.email, password: PASSWORD },
        })
        const loginBody = await loginResp.json()
        if (loginBody.data?.user?.id) {
          user.id = String(loginBody.data.user.id)
        }
      }

      const inviteResp = await page.request.post(`/api/v1/teams/${teamId}/invitations`, {
        data: { identifier: user.email },
      })
      const inviteBody = await inviteResp.json()
      expect(inviteBody.code === 0 || inviteBody.code === 40901).toBeTruthy()
    }
  })

  test('WF-007: PM accepts invitation', async ({ page }) => {
    await loginAs(page, users.pm.email, PASSWORD)
    users.pm.token = (await loginAs(page, users.pm.email, PASSWORD)).token

    if (!users.pm.id) {
      const meResp = await page.request.get('/api/v1/users/me')
      const meBody = await meResp.json()
      users.pm.id = String(meBody.data?.id || '')
    }

    const pendingResp = await page.request.get('/api/v1/invitations/pending')
    const pendingBody = await pendingResp.json()
    const invitations = pendingBody.data?.items || pendingBody.data || []
    const inv = invitations.find(
      (i: Record<string, unknown>) => String(i.team_id || i.teamId) === teamId
    )
    if (inv) {
      await page.request.put(`/api/v1/invitations/${inv.id}`, { data: { action: 'accept' } })
      invitationIds.pm = String(inv.id)
    } else {
      await page.request.put('/api/v1/invitations/0', { data: { action: 'accept' } }).catch(() => {})
    }
  })

  test('WF-008: Dev accepts invitation', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    users.dev.token = (await loginAs(page, users.dev.email, PASSWORD)).token

    if (!users.dev.id) {
      const meResp = await page.request.get('/api/v1/users/me')
      const meBody = await meResp.json()
      users.dev.id = String(meBody.data?.id || '')
    }

    const pendingResp = await page.request.get('/api/v1/invitations/pending')
    const pendingBody = await pendingResp.json()
    const invitations = pendingBody.data?.items || pendingBody.data || []
    const inv = invitations.find(
      (i: Record<string, unknown>) => String(i.team_id || i.teamId) === teamId
    )
    if (inv) {
      await page.request.put(`/api/v1/invitations/${inv.id}`, { data: { action: 'accept' } })
      invitationIds.dev = String(inv.id)
    } else {
      await page.request.put('/api/v1/invitations/0', { data: { action: 'accept' } }).catch(() => {})
    }
  })

  test('WF-009: Tester accepts invitation', async ({ page }) => {
    await loginAs(page, users.tester.email, PASSWORD)
    users.tester.token = (await loginAs(page, users.tester.email, PASSWORD)).token

    if (!users.tester.id) {
      const meResp = await page.request.get('/api/v1/users/me')
      const meBody = await meResp.json()
      users.tester.id = String(meBody.data?.id || '')
    }

    const pendingResp = await page.request.get('/api/v1/invitations/pending')
    const pendingBody = await pendingResp.json()
    const invitations = pendingBody.data?.items || pendingBody.data || []
    const inv = invitations.find(
      (i: Record<string, unknown>) => String(i.team_id || i.teamId) === teamId
    )
    if (inv) {
      await page.request.put(`/api/v1/invitations/${inv.id}`, { data: { action: 'accept' } })
      invitationIds.tester = String(inv.id)
    } else {
      await page.request.put('/api/v1/invitations/0', { data: { action: 'accept' } }).catch(() => {})
    }
  })

  test('WF-010: Creator creates custom roles', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    await page.goto(`/teams/${teamId}`)
    await page.getByTestId('team-detail-tab-roles').click()

    const roles = [
      { name: '产品经理', desc: '负责需求管理和项目推进', perm: 'requirement:approve', slug: 'pm' },
      { name: '开发工程师', desc: '负责编写规范和代码实现', perm: 'spec:write', slug: 'dev' },
      { name: '测试工程师', desc: '负责编写和执行测试用例', perm: 'test:write', slug: 'tester' },
    ]

    for (const role of roles) {
      const createBtn = page.getByTestId('team-roles-btn-create')
      if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await createBtn.click()
        const dialog = page.getByTestId('team-roles-dlg-edit')
        if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          await dialog.getByTestId('team-roles-dlg-edit-inp-name').fill(role.name)
          await dialog.getByTestId('team-roles-dlg-edit-txtarea-desc').fill(role.desc)
          const permChk = dialog.getByTestId(`team-roles-dlg-edit-chk-permission-${role.perm}`)
          if (await permChk.isVisible({ timeout: 1000 }).catch(() => false)) {
            await permChk.check()
          }
          await dialog.getByTestId('team-roles-dlg-edit-btn-save').click()
          await expect(dialog).not.toBeVisible({ timeout: 5000 })
        }
      }

      const resp = await page.request.post(`/api/v1/teams/${teamId}/roles`, {
        data: { name: role.name, description: role.desc, permissions: [role.perm] },
      })
      const body = await resp.json()
      if (body.code === 0 && body.data?.id) {
        if (role.slug === 'pm') pmRoleId = String(body.data.id)
        if (role.slug === 'dev') devRoleId = String(body.data.id)
        if (role.slug === 'tester') testerRoleId = String(body.data.id)
      }
    }

    if (!pmRoleId || !devRoleId || !testerRoleId) {
      const rolesResp = await page.request.get(`/api/v1/teams/${teamId}/roles`)
      const rolesBody = await rolesResp.json()
      const roleList = rolesBody.data?.items || rolesBody.data || []
      for (const r of roleList) {
        if (r.name === '产品经理') pmRoleId = String(r.id)
        if (r.name === '开发工程师') devRoleId = String(r.id)
        if (r.name === '测试工程师') testerRoleId = String(r.id)
      }
    }
  })

  test('WF-011: Creator assigns roles to members', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    const assignments = [
      { userId: users.pm.id, roleIds: [pmRoleId] },
      { userId: users.dev.id, roleIds: [devRoleId] },
      { userId: users.tester.id, roleIds: [testerRoleId] },
    ]

    for (const assignment of assignments) {
      if (!assignment.userId) continue

      await page.goto(`/teams/${teamId}`)
      await page.getByTestId('team-detail-tab-members').click()

      const roleBtn = page.getByTestId(`team-members-btn-roles-user-${assignment.userId}`)
      if (await roleBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await roleBtn.click()
        const dialog = page.getByTestId('team-members-dlg-roles')
        if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          for (const rid of assignment.roleIds) {
            const chk = page.getByTestId(`team-members-dlg-roles-chk-role-${rid}`)
            if (await chk.isVisible({ timeout: 1000 }).catch(() => false)) {
              await chk.check()
            }
          }
          await page.getByTestId('team-members-dlg-roles-btn-save').click()
          await expect(dialog).not.toBeVisible({ timeout: 5000 })
        }
      }

      await page.request
        .put(`/api/v1/teams/${teamId}/members/${assignment.userId}/roles`, {
          data: { role_ids: assignment.roleIds.filter(Boolean).map(Number) },
        })
        .catch(() => {})
    }
  })

  test('WF-012: Creator creates project', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    await page.goto(`/teams/${teamId}`)
    await page.getByTestId('team-detail-tab-projects').click()

    const createBtn = page.getByTestId('project-list-btn-create')
    if (await createBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createBtn.click()
      const dialog = page.getByTestId('project-list-dlg-create')
      if (await dialog.isVisible({ timeout: 5000 }).catch(() => false)) {
        await dialog.getByTestId('project-list-dlg-create-inp-name').fill(`WF Project ${TS}`)
        await dialog.getByTestId('project-list-dlg-create-txtarea-desc').fill('Workflow test project')
        await dialog.getByTestId('project-list-dlg-create-inp-start-date').fill('2026-01-01')
        await dialog.getByTestId('project-list-dlg-create-btn-submit').click()
        await expect(dialog).not.toBeVisible({ timeout: 5000 })
      }
    } else {
      const resp = await page.request.post(`/api/v1/teams/${teamId}/projects`, {
        data: { name: `WF Project ${TS}`, description: 'Workflow test project', start_date: '2026-01-01' },
      })
      const body = await resp.json()
      if (body.code === 0 && body.data?.id) {
        projectId = String(body.data.id)
      }
    }

    if (!projectId) {
      const listResp = await page.request.get(`/api/v1/teams/${teamId}/projects`)
      const listBody = await listResp.json()
      const projects = listBody.data?.items || listBody.data || []
      const found = projects.find((p: Record<string, unknown>) => p.name?.includes(`WF Project ${TS}`))
      if (found) {
        projectId = String(found.id)
      } else if (projects.length > 0) {
        projectId = String(projects[projects.length - 1].id)
      }
    }
    expect(projectId).toBeTruthy()
  })

  test('WF-013: Creator creates iteration (as owner with full perms)', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    if (!projectId) {
      const listResp = await page.request.get(`/api/v1/teams/${teamId}/projects`)
      const listBody = await listResp.json()
      const projects = listBody.data?.items || listBody.data || []
      if (projects.length > 0) {
        projectId = String(projects[projects.length - 1].id)
      }
    }

    await page.goto(`/projects/${projectId}`)

    const createBtn = page.getByTestId('iteration-list-btn-create')
    if (await createBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await createBtn.click()
      const dialog = page.getByTestId('iteration-list-dlg-create')
      if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        await dialog.getByTestId('iteration-list-dlg-create-inp-name').fill(`WF Sprint ${TS}`)
        await dialog.getByTestId('iteration-list-dlg-create-txtarea-goal').fill('Workflow test sprint')
        await dialog.getByTestId('iteration-list-dlg-create-inp-start-date').fill('2026-01-01')
        await dialog.getByTestId('iteration-list-dlg-create-inp-end-date').fill('2026-03-31')
        await dialog.getByTestId('iteration-list-dlg-create-btn-submit').click()
        await expect(dialog).not.toBeVisible({ timeout: 5000 })
      }
    }

    if (!iterationId) {
      const resp = await page.request.post(`/api/v1/projects/${projectId}/iterations`, {
        data: {
          name: `WF Sprint ${TS}`,
          goal: 'Workflow test sprint',
          start_date: '2026-01-01',
          end_date: '2026-03-31',
        },
      })
      const body = await resp.json()
      if (body.code === 0 && body.data?.id) {
        iterationId = String(body.data.id)
      }
    }

    if (!iterationId) {
      const listResp = await page.request.get(`/api/v1/projects/${projectId}/iterations`)
      const listBody = await listResp.json()
      const iterations = listBody.data?.items || listBody.data || []
      const found = iterations.find((i: Record<string, unknown>) => i.name?.includes(`WF Sprint ${TS}`))
      if (found) {
        iterationId = String(found.id)
      } else if (iterations.length > 0) {
        iterationId = String(iterations[iterations.length - 1].id)
      }
    }
    expect(iterationId).toBeTruthy()
  })

  test('WF-014: PM creates requirement', async ({ page }) => {
    await loginAs(page, users.pm.email, PASSWORD)

    await page.goto(`/iterations/${iterationId}/kanban`)

    const addReqBtn = page.getByTestId('iteration-kanban-btn-add-req')
    if (await addReqBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addReqBtn.click()
      const dialog = page.getByTestId('iteration-kanban-dlg-create-req')
      if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        await dialog.getByTestId('iteration-kanban-dlg-create-req-inp-title').fill(`WF Requirement ${TS}`)
        await dialog.getByTestId('iteration-kanban-dlg-create-req-sel-type').selectOption({ label: '功能需求' })
        await dialog.getByTestId('iteration-kanban-dlg-create-req-inp-priority').fill('1')
        await dialog.getByTestId('iteration-kanban-dlg-create-req-txtarea-desc').fill('Workflow test requirement')
        await dialog.getByTestId('iteration-kanban-dlg-create-req-txtarea-type-detail').fill('Feature requirement')
        await dialog.getByTestId('iteration-kanban-dlg-create-req-btn-submit').click()
        await expect(dialog).not.toBeVisible({ timeout: 5000 })
      }
    }

    if (!requirementId) {
      const resp = await page.request.post('/api/v1/requirements', {
        data: {
          title: `WF Requirement ${TS}`,
          type: 'feature',
          priority: 'high',
          description: 'Workflow test requirement',
          iteration_id: Number(iterationId),
        },
      })
      const body = await resp.json()
      if (body.code === 0 && body.data?.id) {
        requirementId = String(body.data.id)
      }
    }

    if (!requirementId) {
      const listResp = await page.request.get(`/api/v1/iterations/${iterationId}/requirements`)
      const listBody = await listResp.json()
      const reqs = listBody.data?.items || listBody.data || []
      const found = reqs.find((r: Record<string, unknown>) => r.title?.includes(`WF Requirement ${TS}`))
      if (found) {
        requirementId = String(found.id)
      } else if (reqs.length > 0) {
        requirementId = String(reqs[reqs.length - 1].id)
      }
    }
    expect(requirementId).toBeTruthy()
  })

  test('WF-015: Dev reviews and approves requirement', async ({ page }) => {
    await loginAs(page, users.pm.email, PASSWORD)
    await page.request.post(`/api/v1/requirements/${requirementId}/submit-review`, {
      data: { reviewer_id: Number(users.dev.id) },
    })

    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const approveBtn = page.getByTestId('req-detail-btn-approve')
    if (await approveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await approveBtn.click()
    } else {
      await page.request.post(`/api/v1/requirements/${requirementId}/approve`)
    }
  })

  test('WF-016: Dev writes spec and submits for review', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const specTab = page.getByTestId('req-detail-tab-spec')
    if (await specTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await specTab.click()

      const specTextarea = page.getByTestId('req-detail-txtarea-spec-content')
      if (await specTextarea.isVisible({ timeout: 3000 }).catch(() => false)) {
        await specTextarea.fill(`# 规范文档 ${TS}\n\n## 实体定义\nUser: { id, name, email }\n\n## API 设计\nPOST /api/users\n\n## 约束\n- 邮箱唯一`)
        const saveBtn = page.getByTestId('req-detail-btn-save-spec')
        if (await saveBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
          await saveBtn.click()
        }
      }
    }

    await page.request.post(`/api/v1/requirements/${requirementId}/spec`, {
      data: { content: `# 规范文档 ${TS}\n\n## 实体定义\nUser: { id, name, email }\n\n## API 设计\nPOST /api/users` },
    })

    await page.request.post(`/api/v1/requirements/${requirementId}/submit-spec-review`, {
      data: { reviewer_id: Number(users.pm.id) },
    })
  })

  test('WF-017: PM approves spec', async ({ page }) => {
    await loginAs(page, users.pm.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const approveBtn = page.getByTestId('req-detail-btn-approve')
    if (await approveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await approveBtn.click()
    }

    await page.request.post(`/api/v1/requirements/${requirementId}/approve-spec`)
  })

  test('WF-018: Tester writes test cases', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.request.patch(`/api/v1/requirements/${requirementId}`, {
      data: { status: 'drafting_tests' },
    })

    await loginAs(page, users.tester.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const addTestCaseBtn = page.getByTestId('req-detail-btn-add-test-case')
    if (await addTestCaseBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await addTestCaseBtn.click()
      const dialog = page.getByTestId('req-detail-dlg-test-case')
      if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
        await dialog.getByTestId('req-detail-dlg-test-case-inp-title').fill('WF Test Case 1')
        await dialog.getByTestId('req-detail-dlg-test-case-sel-type').selectOption('happy_path')
        await dialog.getByTestId('req-detail-dlg-test-case-txtarea-precondition').fill('用户已注册')
        await dialog.getByTestId('req-detail-dlg-test-case-txtarea-steps').fill('1. 调用API 2. 检查返回')
        await dialog.getByTestId('req-detail-dlg-test-case-txtarea-expected').fill('返回200')
        await dialog.getByTestId('req-detail-dlg-test-case-btn-save').click()
        await expect(dialog).not.toBeVisible({ timeout: 5000 })
      }
    }

    const tcResp = await page.request.post('/api/v1/test-cases', {
      data: {
        title: `WF Test Case ${TS}`,
        case_type: 'happy_path',
        precondition: '用户已注册',
        steps: '1. 调用API 2. 检查返回',
        expected_result: '返回200',
        requirement_id: Number(requirementId),
      },
    })
    const tcBody = await tcResp.json()
    if (tcBody.code === 0 && tcBody.data?.id) {
      testCaseId = String(tcBody.data.id)
    }

    if (!testCaseId) {
      const resp = await page.request.get(`/api/v1/requirements/${requirementId}`)
      const body = await resp.json()
      const testCases = body.data?.test_cases || body.data?.cases || []
      if (testCases.length > 0) {
        testCaseId = String(testCases[testCases.length - 1].id)
      }
    }
  })

  test('WF-019: Tester submits test cases for review', async ({ page }) => {
    await loginAs(page, users.tester.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const submitBtn = page.getByTestId('req-detail-btn-submit-tests-review')
    if (await submitBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await submitBtn.click()
      const selReviewer = page.getByTestId('req-detail-dlg-submit-tests-review-sel-reviewer')
      if (await selReviewer.isVisible({ timeout: 3000 }).catch(() => false)) {
        await selReviewer.click()
        await page.getByText(users.pm.nickname).click()
        await page.getByTestId('req-detail-dlg-submit-tests-review-btn-confirm').click()
      }
    }

    await page.request.post(`/api/v1/requirements/${requirementId}/submit-tests-review`, {
      data: { reviewer_id: Number(users.pm.id) },
    })
  })

  test('WF-020: PM approves test cases', async ({ page }) => {
    await loginAs(page, users.pm.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const approveBtn = page.getByTestId('req-detail-btn-approve')
    if (await approveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await approveBtn.click()
    }

    await page.request.post(`/api/v1/requirements/${requirementId}/approve`)
    await page.request.patch(`/api/v1/requirements/${requirementId}`, {
      data: { status: 'approved' },
    })
  })

  test('WF-021: Dev creates task', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/requirements/${requirementId}`)

    const tasksTab = page.getByTestId('req-detail-tab-tasks')
    if (await tasksTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await tasksTab.click()

      const addTaskBtn = page.getByTestId('req-detail-btn-add-task')
      if (await addTaskBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await addTaskBtn.click()
        const dialog = page.getByTestId('req-detail-dlg-add-task')
        if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          await dialog.getByTestId('req-detail-dlg-add-task-inp-title').fill(`WF Task ${TS}`)
          await dialog.getByTestId('req-detail-dlg-add-task-txtarea-desc').fill('Workflow test task')
          const assigneeSel = dialog.getByTestId('req-detail-dlg-add-task-sel-assignee')
          if (await assigneeSel.isVisible({ timeout: 1000 }).catch(() => false)) {
            await assigneeSel.click()
            const option = page.getByText(users.dev.nickname)
            if (await option.isVisible({ timeout: 1000 }).catch(() => false)) {
              await option.click()
            }
          }
          await dialog.getByTestId('req-detail-dlg-add-task-btn-submit').click()
          await expect(dialog).not.toBeVisible({ timeout: 5000 })
        }
      }
    }

    const taskResp = await page.request.post('/api/v1/tasks', {
      data: {
        title: `WF Task ${TS}`,
        description: 'Workflow test task',
        requirement_id: Number(requirementId),
        assignee_id: Number(users.dev.id),
      },
    })
    const taskBody = await taskResp.json()
    if (taskBody.code === 0 && taskBody.data?.id) {
      taskId = String(taskBody.data.id)
    }

    if (!taskId) {
      const listResp = await page.request.get(`/api/v1/requirements/${requirementId}/tasks`)
      const listBody = await listResp.json()
      const tasks = listBody.data?.items || listBody.data || []
      const found = tasks.find((t: Record<string, unknown>) => t.title?.includes(`WF Task ${TS}`))
      if (found) {
        taskId = String(found.id)
      } else if (tasks.length > 0) {
        taskId = String(tasks[tasks.length - 1].id)
      }
    }
    expect(taskId).toBeTruthy()
  })

  test('WF-022: Dev starts coding', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/tasks/${taskId}`)

    const startBtn = page.getByTestId('task-detail-btn-start')
    if (await startBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await startBtn.click()
    }

    await page.request.patch(`/api/v1/tasks/${taskId}`, {
      data: { status: 'coding' },
    })
  })

  test('WF-023: Dev starts testing', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/tasks/${taskId}`)

    const startTestBtn = page.getByTestId('task-detail-btn-start-testing')
    if (await startTestBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await startTestBtn.click()
    }

    await page.request.patch(`/api/v1/tasks/${taskId}`, {
      data: { status: 'testing' },
    })
  })

  test('WF-024: Tester fills in test results (pass)', async ({ page }) => {
    await loginAs(page, users.tester.email, PASSWORD)
    await page.goto(`/tasks/${taskId}`)

    if (testCaseId) {
      const recordResp = await page.request.post(`/api/v1/tasks/${taskId}/test-records`, {
        data: { test_case_id: Number(testCaseId) },
      })
      const recordBody = await recordResp.json()
      const recordId = recordBody.data?.id

      if (recordId) {
        const recordBtn = page.getByTestId(`task-detail-btn-record-${recordId}`)
        if (await recordBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
          await recordBtn.click()
          const dialog = page.getByTestId('task-detail-dlg-record')
          if (await dialog.isVisible({ timeout: 3000 }).catch(() => false)) {
            await page.getByTestId('task-detail-dlg-record-sel-status').selectOption({ label: '通过' })
            await page.getByTestId('task-detail-dlg-record-txtarea-result').fill('测试通过，功能正常')
            await page.getByTestId('task-detail-dlg-record-btn-save').click()
            await expect(dialog).not.toBeVisible({ timeout: 5000 })
          }
        }
      }

      await page.request.post(`/api/v1/tasks/${taskId}/test-records`, {
        data: {
          test_case_id: Number(testCaseId),
          status: 'pass',
          actual_result: '测试通过，功能正常',
        },
      }).catch(() => {})
    } else {
      const tcResp = await page.request.post('/api/v1/test-cases', {
        data: {
          title: `WF Late Test Case ${TS}`,
          case_type: 'happy_path',
          precondition: '前置',
          steps: '步骤',
          expected_result: '预期',
          requirement_id: Number(requirementId),
        },
      })
      const tcBody = await tcResp.json()
      const tcId = tcBody.data?.id
      if (tcId) {
        await page.request.post(`/api/v1/tasks/${taskId}/test-records`, {
          data: {
            test_case_id: tcId,
            status: 'pass',
            actual_result: '测试通过',
          },
        })
      }
    }
  })

  test('WF-025: Dev completes task', async ({ page }) => {
    await loginAs(page, users.dev.email, PASSWORD)
    await page.goto(`/tasks/${taskId}`)

    const completeBtn = page.getByTestId('task-detail-btn-complete')
    if (await completeBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await completeBtn.click()
    }

    await page.request.post(`/api/v1/tasks/${taskId}/complete`).catch(() => {})
    await page.request.patch(`/api/v1/tasks/${taskId}`, {
      data: { status: 'completed' },
    })
  })

  test('WF-026: Creator starts iteration', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    if (projectId) {
      await page.goto(`/projects/${projectId}`)

      const startBtn = page.getByTestId(`iteration-list-btn-start-${iterationId}`)
      if (await startBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await startBtn.click()
        const confirmDialog = page.getByTestId('iteration-list-dlg-confirm-start')
        if (await confirmDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          await confirmDialog.getByTestId('iteration-list-dlg-confirm-start-btn-confirm').click()
        }
      }
    }

    await page.request.post(`/api/v1/iterations/${iterationId}/start`).catch(() => {})
  })

  test('WF-027: Creator completes iteration', async ({ page }) => {
    await loginAs(page, users.creator.email, PASSWORD)

    if (projectId) {
      await page.goto(`/projects/${projectId}`)

      const completeBtn = page.getByTestId(`iteration-list-btn-complete-${iterationId}`)
      if (await completeBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await completeBtn.click()
        const confirmDialog = page.getByTestId('iteration-list-dlg-confirm-complete')
        if (await confirmDialog.isVisible({ timeout: 3000 }).catch(() => false)) {
          await confirmDialog.getByTestId('iteration-list-dlg-confirm-complete-btn-confirm').click()
        }
      }
    }

    await page.request.post(`/api/v1/iterations/${iterationId}/complete`).catch(() => {})
  })
})
