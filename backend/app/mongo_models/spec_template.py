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
    json_schema: dict[str, Any] | None = None


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
                    {
                        "name": "fields",
                        "display_name": "字段列表",
                        "type": "list",
                        "required": True,
                        "description": "实体包含的字段定义（字段名、类型、约束）",
                        "json_schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "fields"],
                                "properties": {
                                    "name": {"type": "string", "minLength": 1},
                                    "description": {"type": "string"},
                                    "fields": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "type"],
                                            "properties": {
                                                "name": {"type": "string", "minLength": 1},
                                                "type": {"type": "string", "minLength": 1},
                                                "constraints": {"type": "array", "items": {"type": "string"}},
                                            },
                                        },
                                        "minItems": 1,
                                    },
                                },
                            },
                        },
                    },
                ],
            },
            {
                "name": "table_design",
                "display_name": "数据表设计",
                "required": True,
                "fields": [
                    {
                        "name": "tables",
                        "display_name": "表列表",
                        "type": "list",
                        "required": True,
                        "description": "每个表的表名、字段、类型、索引、外键关系",
                        "json_schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "fields"],
                                "properties": {
                                    "name": {"type": "string", "minLength": 1},
                                    "description": {"type": "string"},
                                    "fields": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "type"],
                                            "properties": {
                                                "name": {"type": "string", "minLength": 1},
                                                "type": {"type": "string", "minLength": 1},
                                                "nullable": {"type": "boolean"},
                                                "default": {},
                                                "comment": {"type": "string"},
                                            },
                                        },
                                        "minItems": 1,
                                    },
                                    "indexes": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "fields"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "fields": {"type": "array", "items": {"type": "string"}},
                                                "unique": {"type": "boolean"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                ],
            },
            {
                "name": "page_structure",
                "display_name": "页面结构",
                "required": True,
                "fields": [
                    {
                        "name": "pages",
                        "display_name": "页面列表",
                        "type": "list",
                        "required": True,
                        "description": "每个页面的名称、编码、元素列表（含唯一编码）、交互行为",
                        "json_schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "code", "elements"],
                                "properties": {
                                    "name": {"type": "string", "minLength": 1},
                                    "code": {"type": "string", "minLength": 1},
                                    "route": {"type": "string"},
                                    "elements": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["code", "type", "label"],
                                            "properties": {
                                                "code": {"type": "string", "minLength": 1},
                                                "type": {"type": "string", "minLength": 1},
                                                "label": {"type": "string", "minLength": 1},
                                                "interaction": {"type": "string"},
                                            },
                                        },
                                    },
                                    "interactions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "trigger": {"type": "string"},
                                                "behavior": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    {"name": "prototype_html", "display_name": "原型图HTML", "type": "text", "required": False, "description": "页面原型图的HTML代码，在规范中以iframe沙箱展示", "json_schema": {"type": "string"}},
                ],
            },
            {
                "name": "api_design",
                "display_name": "API 设计",
                "required": True,
                "fields": [
                    {
                        "name": "endpoints",
                        "display_name": "接口列表",
                        "type": "list",
                        "required": True,
                        "description": "每个接口的 URL、HTTP 方法、请求参数、响应参数、错误码",
                        "json_schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["method", "path", "description"],
                                "properties": {
                                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                                    "path": {"type": "string", "minLength": 1},
                                    "description": {"type": "string", "minLength": 1},
                                    "request_params": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["name", "in", "type"],
                                            "properties": {
                                                "name": {"type": "string"},
                                                "in": {"type": "string", "enum": ["query", "path", "body", "header"]},
                                                "type": {"type": "string"},
                                                "required": {"type": "boolean"},
                                                "description": {"type": "string"},
                                            },
                                        },
                                    },
                                    "response": {"type": "object"},
                                    "errors": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "code": {"type": "integer"},
                                                "message": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
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

    @staticmethod
    def _section_from_dict(data: dict[str, Any]) -> SpecTemplateSection:
        fields = [
            SpecTemplateField(
                name=f.get("name", ""),
                display_name=f.get("display_name", ""),
                type=f.get("type", "text"),
                required=f.get("required", False),
                description=f.get("description"),
                json_schema=f.get("json_schema"),
            )
            for f in data.get("fields", [])
        ]
        return SpecTemplateSection(
            name=data.get("name", ""),
            display_name=data.get("display_name", ""),
            required=data.get("required", True),
            fields=fields,
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
                        {"name": f.name, "display_name": f.display_name, "type": f.type, "required": f.required, "description": f.description, "json_schema": f.json_schema}
                        for f in s.fields
                    ],
                }
                for s in self.sections
            ],
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }
