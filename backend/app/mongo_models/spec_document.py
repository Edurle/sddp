from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SpecDocumentVersion:
    version: int
    content: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    created_by: int | None = None  # FK -> users.id


@dataclass
class SpecDocument:
    collection_name: str = "specification_documents"

    requirement_id: int | None = None  # FK -> requirements.id
    current_version: int = 0
    versions: list[SpecDocumentVersion] = field(default_factory=list)

    INDEXES: list[dict[str, Any]] = field(
        default_factory=lambda: [
            {"keys": [("requirement_id", 1)], "unique": True},
        ],
    )

    def to_document(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "current_version": self.current_version,
            "versions": [
                {
                    "version": v.version,
                    "content": v.content,
                    "created_at": v.created_at,
                    "created_by": v.created_by,
                }
                for v in self.versions
            ],
        }

    def add_version(self, content: dict[str, Any], created_by: int) -> SpecDocumentVersion:
        self.current_version += 1
        version = SpecDocumentVersion(
            version=self.current_version,
            content=content,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
        )
        self.versions.append(version)
        return version
