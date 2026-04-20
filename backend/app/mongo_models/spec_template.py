from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SpecTemplateField:
    name: str
    display_name: str
    type: str  # "text" | "list" | "object"
    required: bool = False
    description: str | None = None


@dataclass
class SpecTemplateSection:
    name: str
    display_name: str
    required: bool = True
    fields: list[SpecTemplateField] = field(default_factory=list)


@dataclass
class SpecTemplate:
    collection_name: str = "specification_templates"

    team_id: int | None = None
    sections: list[SpecTemplateSection] = field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: int | None = None  # FK -> users.id

    INDEXES: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"keys": [("team_id", 1)], "unique": True},
        ],
    )

    DEFAULT_SECTIONS: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "name": "entity_definition",
                "display_name": "实体定义",
                "required": True,
                "fields": [
                    {"name": "description", "display_name": "实体描述", "type": "text", "required": True, "description": "对实体的简要描述"},
                    {"name": "fields", "display_name": "字段列表", "type": "list", "required": True, "description": "实体包含的字段定义（字段名、类型、约束）"},
                ],
            },
            {
                "name": "table_design",
                "display_name": "数据表设计",
                "required": True,
                "fields": [
                    {"name": "tables", "display_name": "表列表", "type": "list", "required": True, "description": "每个表的表名、字段、类型、索引、外键关系"},
                ],
            },
            {
                "name": "page_structure",
                "display_name": "页面结构",
                "required": True,
                "fields": [
                    {"name": "pages", "display_name": "页面列表", "type": "list", "required": True, "description": "每个页面的名称、编码、元素列表（含唯一编码）、交互行为"},
                ],
            },
            {
                "name": "api_design",
                "display_name": "API 设计",
                "required": True,
                "fields": [
                    {"name": "endpoints", "display_name": "接口列表", "type": "list", "required": True, "description": "每个接口的 URL、HTTP 方法、请求参数、响应参数、错误码"},
                ],
            },
            {
                "name": "constraints",
                "display_name": "其他约束",
                "required": False,
                "fields": [
                    {"name": "directory_structure", "display_name": "目录结构", "type": "text", "required": False, "description": "项目目录结构规范"},
                    {"name": "naming_conventions", "display_name": "命名规范", "type": "text", "required": False, "description": "编码命名规范"},
                    {"name": "other", "display_name": "其他约束", "type": "text", "required": False, "description": "其他技术约束"},
                ],
            },
        ],
    )

    def to_document(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "sections": [
                {
                    "name": s.name,
                    "display_name": s.display_name,
                    "required": s.required,
                    "fields": [
                        {"name": f.name, "display_name": f.display_name, "type": f.type, "required": f.required, "description": f.description}
                        for f in s.fields
                    ],
                }
                for s in self.sections
            ],
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }
