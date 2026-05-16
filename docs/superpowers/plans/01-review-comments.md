# Plan 1: Review Comments

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Add comment support to reviews and display review history timeline on the frontend.

**Spec section:** "1. Review Enhancement" in `docs/superpowers/specs/2026-05-16-agent-collaboration-design.md`

---

### Task 1.1: Create ReviewComment Model

**Files:**
- Create: `backend/app/models/review_comment.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create the model file**

```python
# backend/app/models/review_comment.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewComment(Base):
    __tablename__ = "review_comments"
    __table_args__ = (
        Index("idx_rc_requirement", "requirement_id"),
        Index("idx_rc_reviewer", "reviewer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(nullable=False)
    reviewer_id: Mapped[int] = mapped_column(nullable=False)
    review_type: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
```

- [ ] **Step 2: Register in models/__init__.py**

Add import and export for `ReviewComment` in `backend/app/models/__init__.py`:

After line `from app.models.spec import SpecTemplate, SpecDocument`, add:
```python
from app.models.review_comment import ReviewComment
```

Add `"ReviewComment"` to `__all__`.

- [ ] **Step 3: Run test to verify model loads**

Run: `conda run -n sdd python -c "from app.models import ReviewComment; print('OK')"`
Expected: `OK`

---

### Task 1.2: Create Alembic Migration

**Files:**
- Create: `backend/alembic/versions/xxxx_add_review_comments.py`

- [ ] **Step 1: Generate migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini revision --autogenerate -m "add review_comments table" --rev-id $(python3 -c "import random; print(format(random.randint(0,0xffffff),'06x'))")`
(workdir: repo root)

If autogenerate doesn't pick it up, write manually. The migration file must contain:

```python
def upgrade() -> None:
    op.create_table(
        'review_comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('requirement_id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('review_type', sa.String(length=20), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_rc_requirement', 'review_comments', ['requirement_id'])
    op.create_index('idx_rc_reviewer', 'review_comments', ['reviewer_id'])


def downgrade() -> None:
    op.drop_index('idx_rc_reviewer', table_name='review_comments')
    op.drop_index('idx_rc_requirement', table_name='review_comments')
    op.drop_table('review_comments')
```

Set `down_revision` to `'a3a8bc997520'` (the spec tables migration).

- [ ] **Step 2: Run migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini upgrade head`
(workdir: repo root)
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/review_comment.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat: add ReviewComment model and migration"
```

---

### Task 1.3: Review Comment Service

**Files:**
- Create: `backend/app/services/review_comment.py`

- [ ] **Step 1: Create service with list + create functions**

```python
# backend/app/services/review_comment.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReviewComment


async def create_review_comment(
    db: AsyncSession,
    requirement_id: int,
    reviewer_id: int,
    review_type: str,
    action: str,
    comment: str | None = None,
) -> dict:
    rc = ReviewComment(
        requirement_id=requirement_id,
        reviewer_id=reviewer_id,
        review_type=review_type,
        action=action,
        comment=comment,
    )
    db.add(rc)
    await db.flush()
    await db.refresh(rc)
    return _to_dict(rc)


async def list_review_comments(
    db: AsyncSession,
    requirement_id: int,
) -> list[dict]:
    stmt = (
        select(ReviewComment)
        .where(ReviewComment.requirement_id == requirement_id)
        .order_by(ReviewComment.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_to_dict(r) for r in rows]


def _to_dict(rc: ReviewComment) -> dict:
    return {
        "id": rc.id,
        "requirement_id": rc.requirement_id,
        "reviewer_id": rc.reviewer_id,
        "review_type": rc.review_type,
        "action": rc.action,
        "comment": rc.comment,
        "created_at": rc.created_at.isoformat() if rc.created_at else None,
    }
```

- [ ] **Step 2: Verify import**

Run: `conda run -n sdd python -c "from app.services.review_comment import create_review_comment, list_review_comments; print('OK')"`
Expected: `OK`

---

### Task 1.4: Add Review Comment API Endpoint

**Files:**
- Modify: `backend/app/api/requirements.py`

- [ ] **Step 1: Add GET endpoint for review comments**

In `backend/app/api/requirements.py`, add a new import at the top:

```python
from app.services import review_comment as rc_svc
```

Add this endpoint after the existing `review_requirement` endpoint (after line 517):

```python
@router.get("/{id}/review-comments")
async def get_review_comments(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await rc_svc.list_review_comments(db, id)
    return {"code": 0, "message": "success", "data": data}
```

- [ ] **Step 2: Modify review_requirement service to create ReviewComment records**

In `backend/app/services/requirement.py`, in the `review_requirement` function (around line 285-298), after setting `review.status` and `review.comment`, add a call to create a ReviewComment record.

Add import at top:
```python
from app.services import review_comment as rc_svc
```

After `review.reviewed_at = datetime.now(timezone.utc)` (line 297), add:
```python
    await rc_svc.create_review_comment(
        db, req.id, user_id, review.review_type, action, comment,
    )
```

- [ ] **Step 3: Write test**

Create `backend/tests/test_review_comments.py`:

```python
import pytest
from tests.conftest import auth_headers


class TestReviewComments:
    @pytest.mark.asyncio
    async def test_approve_creates_review_comment(
        self, client, normal_user, another_user, sample_iteration, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:review_req"])
        submit_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert submit_resp.status_code == 200

        reviewer_headers = auth_headers(another_user.id)
        review_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve", "comment": "看起来不错"},
            headers=reviewer_headers,
        )
        assert review_resp.status_code == 200

        comments_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        assert comments_resp.status_code == 200
        body = comments_resp.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["action"] == "approve"
        assert body["data"][0]["comment"] == "看起来不错"
        assert body["data"][0]["reviewer_id"] == another_user.id

    @pytest.mark.asyncio
    async def test_reject_creates_review_comment(
        self, client, normal_user, another_user, sample_iteration, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:review_req"])
        await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )

        reviewer_headers = auth_headers(another_user.id)
        await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": "需要修改"},
            headers=reviewer_headers,
        )

        comments_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        body = comments_resp.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["action"] == "reject"
        assert body["data"][0]["comment"] == "需要修改"

    @pytest.mark.asyncio
    async def test_empty_comments_list(
        self, client, normal_user, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == []
```

- [ ] **Step 4: Update conftest TRUNCATE to include review_comments**

In `backend/tests/conftest.py`, update `_TRUNCATE_SQL` (line 34-42). Add `review_comments` before `requirement_reviews`:

```python
_TRUNCATE_SQL = text(
    "TRUNCATE TABLE "
    "review_comments, "
    "test_execution_records, test_execution_rounds, test_cases, tasks, "
    "requirement_reviews, requirements, spec_documents, spec_templates, "
    "iterations, projects, "
    "member_roles, role_permissions, roles, team_members, invitations, "
    "password_reset_tokens, api_keys, teams, users "
    "RESTART IDENTITY CASCADE"
)
```

- [ ] **Step 5: Run tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_review_comments.py -v`
Expected: All 3 tests pass

- [ ] **Step 6: Run full backend test suite**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --timeout=60`
Expected: All tests pass (0 failures)

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/review_comment.py backend/app/api/requirements.py backend/app/services/requirement.py backend/tests/test_review_comments.py backend/tests/conftest.py
git commit -m "feat: add review comments API and auto-record on review"
```

---

### Task 1.5: Frontend — Review Comment Timeline

**Files:**
- Modify: `frontend/src/views/requirement/RequirementDetailPage.vue`

This task adds:
1. A review comment input in the approve/reject dialog
2. A review history timeline below the sidebar actions

- [ ] **Step 1: Add reviewComments ref and fetch function**

In the `<script setup>` section, add a new ref and fetch function:

```typescript
const reviewComments = ref<Array<{ id: number; reviewer_id: number; action: string; comment: string | null; created_at: string }>>([])

async function fetchReviewComments() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/review-comments`)
    reviewComments.value = res.data?.data || []
  } catch {
    reviewComments.value = []
  }
}
```

Call `fetchReviewComments()` inside the existing `fetchRequirement()` after data is loaded.

- [ ] **Step 2: Add comment input to reject dialog**

Find the existing reject dialog (it should have a text input for the rejection reason). Ensure it stores the value in a ref like `rejectComment`. The existing reject flow already requires a comment for rejection per the backend logic.

- [ ] **Step 3: Add review timeline in the sidebar**

After the action buttons section in `RequirementSidebar.vue` (or in the detail page sidebar area), add:

```html
<div v-if="reviewComments.length > 0" class="review-timeline">
  <h4>审核历史</h4>
  <div v-for="rc in reviewComments" :key="rc.id" class="review-timeline-item">
    <div class="review-timeline-dot" :class="rc.action === 'approve' ? 'dot-approve' : 'dot-reject'"></div>
    <div class="review-timeline-content">
      <div class="review-timeline-header">
        <span class="review-timeline-action" :class="rc.action">{{ rc.action === 'approve' ? '通过' : '拒绝' }}</span>
        <span class="review-timeline-time">{{ formatTime(rc.created_at) }}</span>
      </div>
      <div v-if="rc.comment" class="review-timeline-comment">{{ rc.comment }}</div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: Add styles for the timeline**

```css
.review-timeline {
  margin-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 16px;
}
.review-timeline h4 {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}
.review-timeline-item {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.review-timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.dot-approve { background: #22c55e; }
.dot-reject { background: #ef4444; }
.review-timeline-content {
  flex: 1;
  min-width: 0;
}
.review-timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.review-timeline-action {
  font-size: 12px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.review-timeline-action.approve {
  background: #dcfce7;
  color: #166534;
}
.review-timeline-action.reject {
  background: #fef2f2;
  color: #991b1b;
}
.review-timeline-time {
  font-size: 11px;
  color: #aaa;
  white-space: nowrap;
}
.review-timeline-comment {
  font-size: 13px;
  color: #555;
  word-break: break-word;
}
```

- [ ] **Step 5: Add formatTime helper**

```typescript
function formatTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
```

- [ ] **Step 6: Build frontend**

Run: `cd frontend && npx vue-tsc -b && npx vite build`
Expected: Build succeeds (only pre-existing TS errors are acceptable)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/requirement/
git commit -m "feat: add review comment timeline to requirement detail"
```

---

### Task 1.6: Verify All Backend Tests Still Pass

- [ ] **Step 1: Full test suite**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --timeout=60`
Expected: All tests pass

- [ ] **Step 2: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: review comments integration fixes"
```
