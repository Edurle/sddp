# E2E 测试策略设计：getByRole + Page Object + 语义化规范

## 问题

引入前端组件库（Element Plus、Ant Design Vue 等）后，组件内部 DOM 层级阻隔 `data-testid`，导致 Playwright 无法穿透定位目标元素。需要一套通用的、与组件库无关的 E2E 测试定位策略。

## 方案选择

| 方案 | 思路 | 与组件库耦合 | 维护成本 |
|------|------|-------------|---------|
| A: getByRole + Page Object | 用 ARIA 角色定位，Page Object 封装细节 | 无 | 低 |
| B: Wrapper 组件透传 testid | 对每个组件库组件封装 wrapper | 高 | 高 |
| C: Locator 链 + 语义 CSS | 链式 locator + CSS 选择器 | 中 | 中 |

**选择方案 A**。理由：主流组件库均遵循 WAI-ARIA 规范，`getByRole` 可靠且与框架无关（Vue 2 / Vue 3 / React 通用），Page Object 隔离了 DOM 实现细节。

## 核心原则

### 定位器优先级

| 优先级 | 定位器 | 场景 |
|--------|--------|------|
| 1 | `getByRole()` | 交互元素（按钮、链接、输入框、对话框） |
| 2 | `getByLabel()` | 表单输入字段 |
| 3 | `getByPlaceholder()` | 无 label 的输入框 |
| 4 | `getByText()` | 静态文本、非交互元素 |
| 5 | `getByTestId()` | 兜底：无语义展示元素、同名元素消歧 |

### data-testid 的角色

testid **不废弃**，从"主力定位器"变为"兜底定位器"。适用场景：

- 纯展示元素（统计数字卡片、状态标签）无 ARIA 角色
- 页面有多个同名按钮（两个"提交"），需要 testid 消歧
- 列表中的第 N 项，testid 比 locator 链更稳定

## getByRole 详解

### ARIA Role 与 HTML 元素的隐含映射

```
<button>              → role="button"
<a href="...">        → role="link"
<input>               → role="textbox"
<select>              → role="combobox" / "listbox"
<table>               → role="table"
<tr>                  → role="row"
<td>                  → role="cell"
<th>                  → role="columnheader"
<h1>~<h6>            → role="heading"
<div role="dialog">   → role="dialog"
<ul>/<ol>             → role="list"
<li>                  → role="listitem"
```

### Accessible Name 计算规则（优先级从高到低）

| 来源 | 示例 |
|------|------|
| `aria-label` | `<button aria-label="关闭">` |
| `aria-labelledby` | `<button aria-labelledby="lbl">` |
| 关联 `<label>` | `<label for="email">邮箱</label><input id="email">` |
| 内部文本 | `<button>提交审核</button>` → name="提交审核" |
| `alt` / `title` | `<img alt="Logo">` → name="Logo" |
| `placeholder` | `<input placeholder="请输入邮箱">` |

### 组件库 Role 映射（通用，Vue/React 均适用）

```
Button 组件       → <button>              → getByRole('button')
Input 组件        → <input>               → getByRole('textbox')
Select 组件       → <input role=combobox>  → getByRole('combobox')
Select 选项       → <li role=option>       → getByRole('option', { name })
Dialog 组件       → <div role=dialog>      → getByRole('dialog')
Table 组件        → <table>               → getByRole('table')
Checkbox 组件     → <input type=checkbox>  → getByRole('checkbox')
Tab 组件          → <div role=tab>         → getByRole('tab')
Tab 面板          → <div role=tabpanel>    → getByRole('tabpanel')
Alert 组件        → <div role=alert>       → getByRole('alert')
Link 组件         → <a>                    → getByRole('link')
```

## 各场景定位策略

### Select 下拉选择

```typescript
await page.getByRole('combobox', { name: '审核人' }).click()
await page.getByRole('option', { name: '张三' }).click()
```

组件库将选项 teleport 到 body 底部不影响，`getByRole` 搜索整个文档。

### Table 行操作

```typescript
const table = page.getByRole('table', { name: '任务列表' })
const row = table.getByRole('row').filter({ hasText: '实现用户 API' })
await row.getByRole('button', { name: '编辑' }).click()

// 按列头索引定位单元格
const headers = await table.getByRole('columnheader').allTextContents()
const statusIdx = headers.indexOf('状态')
const cell = row.getByRole('cell').nth(statusIdx)
```

### Dialog 内部操作

```typescript
const dialog = page.getByRole('dialog', { name: '提交审核' })
await dialog.getByRole('combobox', { name: '审核人' }).click()
await page.getByRole('option', { name: '李四' }).click()
await dialog.getByRole('button', { name: '确认' }).click()
```

### Form 填写 + 校验消息

```typescript
await page.getByLabel('邮箱').fill('test@example.com')
await page.getByRole('button', { name: '注册' }).click()
await expect(page.getByRole('alert').filter({ hasText: '密码' })).toBeVisible()
```

### Tab 切换

```typescript
await page.getByRole('tab', { name: '规范文档' }).click()
await expect(page.getByRole('tabpanel', { name: '规范文档' })).toBeVisible()
```

### 同名按钮消歧

```typescript
// 方式 1：用 region 限定范围
const specSection = page.getByRole('region', { name: '规范' })
await specSection.getByRole('button', { name: '提交' }).click()

// 方式 2：兜底用 testid
await page.getByTestId('btn-submit-spec-review').click()
```

## Page Object 分层架构

```
tests/
├── fixtures/
│   └── auth.ts
├── pages/                         # 页面级 Page Object
│   ├── BasePage.ts                # 通用方法
│   ├── RequirementPage.ts
│   ├── TaskPage.ts
│   ├── DashboardPage.ts
│   └── ...
├── components/                    # 组件级 Helper
│   ├── DialogHelper.ts
│   ├── TableHelper.ts
│   └── SelectHelper.ts
└── requirement.spec.ts
```

### BasePage

```typescript
export class BasePage {
  constructor(protected page: Page) {}

  async goto(path: string) { await this.page.goto(path) }

  getButton(name: string | RegExp) { return this.page.getByRole('button', { name }) }
  getLink(name: string | RegExp)    { return this.page.getByRole('link', { name }) }
  getAlert(name?: string | RegExp)  { return this.page.getByRole('alert', { name }) }
  getHeading(name: string | RegExp) { return this.page.getByRole('heading', { name }) }
}
```

### Component Helpers

```typescript
// SelectHelper
export class SelectHelper {
  constructor(private page: Page) {}
  async select(label: string | RegExp, option: string | RegExp) {
    await this.page.getByRole('combobox', { name: label }).click()
    await this.page.getByRole('option', { name: option }).click()
  }
}

// TableHelper
export class TableHelper {
  private table: Locator
  constructor(page: Page, name?: string | RegExp) {
    this.table = name ? page.getByRole('table', { name }) : page.getByRole('table')
  }
  row(filter: { hasText: string | RegExp }) {
    return this.table.getByRole('row').filter(filter)
  }
  async cellText(rowFilter: string | RegExp, columnName: string): Promise<string> {
    const headers = await this.table.getByRole('columnheader').allTextContents()
    const colIdx = headers.indexOf(columnName)
    return this.table.getByRole('row').filter({ hasText: rowFilter })
      .getByRole('cell').nth(colIdx).innerText()
  }
}

// DialogHelper
export class DialogHelper {
  constructor(private page: Page) {}
  async open(triggerName: string | RegExp): Promise<Locator> {
    await this.page.getByRole('button', { name: triggerName }).click()
    const dialog = this.page.getByRole('dialog')
    await dialog.waitFor({ state: 'visible' })
    return dialog
  }
  async confirm(dialog: Locator) {
    await dialog.getByRole('button', { name: /确认|确定|提交/ }).click()
    await dialog.waitFor({ state: 'hidden' })
  }
}
```

### RequirementPage（页面级）

```typescript
export class RequirementPage extends BasePage {
  private dialog = new DialogHelper(this.page)
  private select = new SelectHelper(this.page)

  async gotoRequirement(id: number) { await this.goto(`/requirements/${id}`) }

  async submitReview(reviewerName: string | RegExp) {
    const dialog = await this.dialog.open('提交审核')
    await this.select.select('审核人', reviewerName)
    await this.dialog.confirm(dialog)
  }

  async reject(reason: string) {
    await this.getButton(/驳回/).click()
    const dialog = this.page.getByRole('dialog')
    await dialog.getByLabel(/理由|备注/).fill(reason)
    await dialog.getByRole('button', { name: /确认/ }).click()
  }

  async addTask(title: string, desc: string, assignee: string | RegExp) {
    await this.page.getByRole('tab', { name: '任务' }).click()
    const dialog = await this.dialog.open('添加任务')
    await dialog.getByLabel('标题').fill(title)
    await dialog.getByLabel('描述').fill(desc)
    await this.select.select('负责人', assignee)
    await this.dialog.confirm(dialog)
  }
}
```

### 测试用例对比

```typescript
// 旧写法（testid）
await authenticatedPage.getByTestId('req-detail-btn-submit-req-review').click()
await expect(authenticatedPage.getByTestId('req-detail-dlg-submit-review')).toBeVisible()
await authenticatedPage.getByTestId('req-detail-dlg-submit-review-sel-reviewer').click()
await authenticatedPage.getByText(reviewer.nickname).click()
await authenticatedPage.getByTestId('req-detail-dlg-submit-review-btn-confirm').click()

// 新写法（Page Object + getByRole）
const reqPage = new RequirementPage(authenticatedPage)
await reqPage.gotoRequirement(req.id)
await reqPage.submitReview(reviewer.nickname)
```

## 规范模板变更

### page_structure elements 新增字段

```diff
  "properties": {
      "code": {"type": "string"},
      "type": {"type": "string"},
      "label": {"type": "string"},
+     "role": {"type": "string"},
+     "accessible_name": {"type": "string"},
      "interaction": {"type": "string"}
  }
```

| 字段 | 含义 | 示例 |
|------|------|------|
| `role` | ARIA 角色 | `button`, `combobox`, `dialog`, `table`, `tab` |
| `accessible_name` | 可访问名称（getByRole 的 name） | `"提交需求审核"`, `"审核人"` |

`agent_prompt` 更新，提示 Agent 填写 role 和 accessible_name。

### 规范示例

```json
{
  "code": "btn-submit-review",
  "type": "button",
  "role": "button",
  "accessible_name": "提交需求审核",
  "label": "提交审核",
  "interaction": "打开选择审核人对话框"
}
```

## 测试用例编写方式变更

测试用例数据模型不变（steps/precondition/expected_result 仍是纯文本）。变的是编写方式：

**旧写法**（引用 code/testid）：
```
1. 点击 [btn-submit-review] 按钮
2. 在 [sel-reviewer] 下拉框选择审核人
```

**新写法**（引用 accessible_name）：
```
1. 点击"提交需求审核"按钮
2. 在"审核人"下拉框选择"张三"
```

### 三方对齐

```
规范 accessible_name     测试用例 steps           Playwright 代码
"提交需求审核"      →   点击"提交需求审核"按钮  →  getByRole('button', { name: '提交需求审核' })
"审核人"            →   在"审核人"下拉框        →  getByRole('combobox', { name: '审核人' })
"任务列表"          →   验证"任务列表"表格       →  getByRole('table', { name: '任务列表' })
```

## 页面实现要求

### 基本规则

- 按钮有可见文本或 `aria-label`
- 输入框通过 `<label>` 或 `aria-label` 关联名称
- 对话框有 `title` 或 `aria-labelledby`（组件库自动处理）
- 表格使用 `aria-label` 标识用途
- Tab 使用组件库的原生 tab 组件（自动获得 role）

### 图标按钮

```vue
<el-button :icon="Delete" aria-label="删除需求" @click="deleteReq" />
```

### 输入框

```vue
<el-form-item label="标题">
  <el-input v-model="form.title" />
</el-form-item>
```

### 表格

```vue
<el-table :data="tasks" aria-label="任务列表">
  <el-table-column prop="title" label="标题" />
</el-table>
```

## 框架无关性

本方案适用于 Vue 2、Vue 3、React，因为 `getByRole` 查询的是渲染后的 DOM 可访问性树：

| 框架 | 组件写法 | 渲染结果 | 定位代码 |
|------|---------|---------|---------|
| Vue 2 | `<el-button>提交</el-button>` | `<button>提交</button>` | `getByRole('button', { name: '提交' })` |
| Vue 3 | `<el-button>提交</el-button>` | `<button>提交</button>` | 同上 |
| React | `<Button>提交</Button>` | `<button>提交</button>` | 同上 |

换框架只换实现层，测试代码不动。

## SDD 平台改动项

| 改动 | 位置 | 说明 |
|------|------|------|
| 规范模板 Schema | `spec_template.py` | elements 增加 role、accessible_name 字段 |
| Agent 提示词 | `spec_template.py` | agent_prompt 更新，要求填写 role 和 accessible_name |
| 规范渲染 | 前端 SpecRenderer | 元素表格增加 role、accessible_name 列 |
| 无需改动 | 测试用例模型 | steps 仍是纯文本 |
| 无需改动 | API / 数据库 | 无结构变化 |

## 迁移策略

| 阶段 | 做法 |
|------|------|
| 新测试 | 直接用 getByRole + Page Object |
| 引入组件库时 | 受影响的测试同步改用 Page Object |
| 旧测试 | 保持 testid 不动，仍可用 |
