# 需求变更与跨迭代关联设计

## 背景

需求通过审核后无法修改。实际场景中，已审核需求可能需要变更，或同一功能在不同迭代中持续优化。需要一种机制支持：
1. 同迭代内需求变更：废弃旧需求，创建新需求替代
2. 跨迭代功能关联：标记不同迭代中针对同一功能的需求

## 设计方案

### 数据模型

**不修改 Requirement 模型**，仅新增 RequirementLink 表：

```python
class RequirementLink(Base):
    __tablename__ = "requirement_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(20), nullable=False)  # supersede | relates_to
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "link_type", name="uq_req_link"),
        Index("idx_link_source", "source_id"),
        Index("idx_link_target", "target_id"),
    )
```

### link_type 语义

| link_type | 含义 | 触发方式 | 约束 |
|-----------|------|----------|------|
| `supersede` | 同迭代变更替代 | POST /supersede 自动创建 | source 必须为 approved，创建后 source → deprecated |
| `relates_to` | 跨迭代同功能关联 | 手动创建 | 无状态限制 |

### 状态流转变更

在现有 `VALID_STATUS_TRANSITIONS` 中增加：
```python
"approved": {"deprecated"},
"deprecated": set(),  # 终态
```

### 链式结构

支持多次变更和跨迭代关联的自然链式结构：

**多次变更（同迭代）**：
```
A →(supersede)→ B →(supersede)→ C
deprecated      deprecated      active
```

**跨迭代优化**：
```
A(iter1) →(relates_to)→ B(iter2) →(relates_to)→ C(iter3)
```

**混合场景**：
```
A(iter1) →(supersede)→ A'(iter1) →(relates_to)→ B(iter2) →(supersede)→ B'(iter2)
deprecated          active          active         deprecated      active
```

查询时遍历 links 找到完整链路。

### API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/requirements/{reqId}/supersede` | 创建变更需求，原需求→deprecated，自动建 supersede link。Body: 可选 title, description, req_type, priority 覆盖默认值 |
| POST | `/requirements/{reqId}/links` | 手动创建关联（relates_to）。Body: target_id, link_type |
| GET | `/requirements/{reqId}/links` | 查询需求的所有关联（双向，包含 source 和 target 方向） |
| DELETE | `/requirements/{reqId}/links/{linkId}` | 删除关联（supersede 类型不可删） |

#### supersede 行为细节

1. 校验原需求状态为 `approved`
2. 创建新需求（同 iteration_id），默认复制 title（加"（变更）"后缀）、req_type、priority
3. 原需求 status → `deprecated`
4. 创建 RequirementLink(source=原需求, target=新需求, link_type=supersede)
5. 返回新需求信息

### 编辑限制

`deprecated` 需求及其关联资源全部锁定：

- 需求：不可编辑、不可删除、不可提交审核
- 规格说明：不可编辑
- 任务：不可编辑、不可删除
- 测试用例：不可编辑、不可删除

### 前端展示

- deprecated 需求显示"已废弃"标签，链接到替代需求
- 新需求显示"变更自 #xxx"链接
- 需求详情页展示关联需求列表，区分 supersede 和 relates_to
- 关联需求可点击跳转

### 数据库迁移

仅新增 `requirement_links` 表，不修改任何现有表结构。Alembic migration 脚本创建新表即可。
