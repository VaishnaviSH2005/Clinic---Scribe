"""Standard response envelope (PRD Ch16.2). All endpoints should return these shapes."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class Pagination(BaseModel):
    page: int
    pageSize: int
    total: int


class ApiListResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T]
    pagination: Pagination
