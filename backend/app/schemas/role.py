from pydantic import BaseModel, ConfigDict, Field


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=32)
    description: str | None = None
    permissions: list[str]


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=32)
    description: str | None = None
    permissions: list[str] | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_builtin: bool = False
    permissions: list[str] = []
    description: str | None = None
