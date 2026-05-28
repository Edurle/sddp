REQ_TYPES = [
    {
        "value": "feature",
        "label": "功能需求",
        "description": "新功能或功能增强",
    },
    {
        "value": "bug",
        "label": "缺陷修复",
        "description": "Bug 修复",
        "type_detail_schema": {
            "reproduce_steps": "复现步骤",
            "environment": "运行环境",
            "severity": "严重程度 (critical/major/minor)",
        },
    },
    {
        "value": "optimization",
        "label": "优化改进",
        "description": "性能优化或体验改进",
        "type_detail_schema": {
            "current_issue": "当前问题",
            "expected_improvement": "预期改进",
            "metrics": "衡量指标",
        },
    },
]

PRIORITY_LEVELS = [
    {"value": 3, "label": "高"},
    {"value": 2, "label": "中"},
    {"value": 1, "label": "低"},
]

SUGGESTIONS = [
    "建议填写 description 以帮助后续规范生成",
    "如果是 bug 类型，建议填写 type_detail 中的 reproduce_steps 和 severity",
    "建议提供 prototype_html 原型图以便规范中的页面设计更准确",
]


def get_requirement_guide() -> dict:
    return {
        "req_types": REQ_TYPES,
        "priority_levels": PRIORITY_LEVELS,
        "required_fields": ["title", "req_type", "priority", "iteration_id"],
        "optional_fields": ["description", "type_detail", "prototype_html"],
        "suggestions": SUGGESTIONS,
    }
