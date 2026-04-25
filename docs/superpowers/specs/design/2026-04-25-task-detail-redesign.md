# 任务详情页重设计 — 双栏布局

## 设计目标

将任务详情页从单列线性布局改为 **左侧边栏 + 右侧主内容区** 的双栏布局，与需求详情页风格保持一致。所有现有 `task-detail-*` testid 原样保留，不破坏任何 E2E 测试。

## 布局结构

```
┌─────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────────────────┐ │
│  │  TaskSidebar  │  │  Main Content Area       │ │
│  │  (260px)      │  │  (flex: 1)               │ │
│  │               │  │                          │ │
│  │  · 进度条     │  │  · 标签栏（下划线风格）   │ │
│  │  · 基本信息   │  │  · 规范 Tab              │ │
│  │  · 操作按钮   │  │  · 测试执行 Tab          │ │
│  └──────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## 左侧边栏 — TaskSidebar.vue

### 进度条
- 4 个步骤竖向排列：未开始 → 编码中 → 测试中 → 已完成
- 当前步骤蓝色高亮 (`#1677ff`)，已完成黑色 + ✓，待进行灰色
- 步骤状态根据 `task.status` 自动计算

### 基本信息卡片
- 标题、描述、状态 badge、指派人、关联需求（蓝色链接可跳转）
- 状态 badge 颜色：pending=灰、coding=紫、testing=橙、completed=绿
- 编辑模式下，标题和描述替换为输入框和文本域

### 操作按钮
- 根据状态条件显示，按钮纵向排列
- 主要操作用蓝色/绿色强调，次要操作灰色，危险操作红色边框
- 编辑模式下只显示"保存"按钮

## 右侧主内容区

### 标签栏
- 下划线风格，与需求详情页一致
- Tab：规范（常驻）、测试执行（仅 testing/completed 状态）

### 规范 Tab
- 只读展示关联需求的规范文档
- 使用等宽字体的代码风格卡片

### 测试执行 Tab
1. **摘要卡片** — 4 格统计：总用例、通过、失败、跳过，颜色区分
2. **测试记录表格** — 用例名、状态（彩色文字）、更新按钮
3. **执行历史** — 圆角按钮式的轮次选择 + 该轮记录表格

## Testid 映射

所有 testid 保持不变，仅 DOM 位置从平铺改为嵌套在双栏布局中：

| 区域 | testid | 新位置 |
|------|--------|--------|
| 侧边栏 | `task-detail-sidebar`（新增） | `<aside>` |
| 状态文本 | `task-detail-txt-status` | 侧边栏进度条下方隐藏兼容元素 + 基本 info 卡片中 badge |
| 标题 | `task-detail-txt-title` | 侧边栏 info 卡片 |
| 描述 | `task-detail-txt-description` | 侧边栏 info 卡片 |
| 指派人 | `task-detail-txt-assignee` | 侧边栏 info 卡片 |
| 关联需求 | `task-detail-txt-linked-requirement` | 侧边栏 info 卡片 |
| 编辑输入 | `task-detail-inp-title`, `task-detail-txtarea-description` | 侧边栏编辑表单 |
| 操作按钮 | `task-detail-btn-start`, `task-detail-btn-start-testing`, `task-detail-btn-complete`, `task-detail-btn-edit`, `task-detail-btn-delete`, `task-detail-btn-save` | 侧边栏操作区 |
| Tab 按钮 | `task-detail-tab-spec`, `task-detail-tab-test-exec` | 主内容区标签栏 |
| 规范内容 | `task-detail-txt-spec-content` | 主内容区规范面板 |
| 测试摘要 | `task-detail-txt-test-summary` | 主内容区摘要卡片 |
| 测试记录表 | `task-detail-tbl-test-records` | 主内容区表格 |
| 记录状态 | `task-detail-txt-record-status-{id}` | 表格行内 |
| 记录按钮 | `task-detail-btn-record-{id}` | 表格行内 |
| 执行历史 | `task-detail-list-exec-rounds`, `task-detail-list-exec-history` | 主内容区历史区 |
| 轮次按钮 | `task-detail-btn-exec-round-{id}` | 主内容区轮次栏 |
| 轮次记录表 | `task-detail-tbl-round-records`, `task-detail-row-record-{id}` | 主内容区 |
| 记录弹窗 | `task-detail-dlg-record`, `task-detail-dlg-record-sel-status`, `task-detail-dlg-record-txtarea-result`, `task-detail-dlg-record-txtarea-reason`, `task-detail-dlg-record-btn-save` | 弹窗不变 |

## 新增 testid

| testid | 用途 |
|--------|------|
| `task-detail-sidebar` | 侧边栏容器，用于验证双栏布局 |
| `task-detail-step-progress` | 进度条容器，用于验证步骤节点 |
| `task-detail-step-progress-step-pending` | 进度条"未开始"步骤节点 |
| `task-detail-step-progress-step-coding` | 进度条"编码中"步骤节点 |
| `task-detail-step-progress-step-testing` | 进度条"测试中"步骤节点 |
| `task-detail-step-progress-step-completed` | 进度条"已完成"步骤节点 |

## 响应式

- ≤768px：侧边栏变为顶部水平布局，边框从右侧改为底部
