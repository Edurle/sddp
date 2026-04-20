ALL_PERMISSIONS = [
    "project:create",
    "project:edit",
    "project:archive",
    "project:delete",
    "iteration:create",
    "iteration:edit",
    "iteration:start",
    "iteration:complete",
    "requirement:create",
    "requirement:edit",
    "requirement:delete",
    "requirement:review_req",
    "requirement:review_spec",
    "requirement:review_tests",
    "task:create",
    "task:edit",
    "task:delete",
    "task:test",
    "task:complete",
    "member:invite",
    "member:remove",
    "member:assign_role",
    "spec_template:edit",
]


def is_valid_permission(permission: str) -> bool:
    return permission in ALL_PERMISSIONS
