from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T | None = None


class PageData(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]


class ErrorResponse(BaseModel):
    code: int
    message: str
    data: None = None
