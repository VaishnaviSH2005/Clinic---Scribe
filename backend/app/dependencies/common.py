"""Shared FastAPI dependencies.

`get_current_user` / role-guard dependencies (PRD Ch7 / Ch18) are added with
the Authentication module. This file only wires the pagination dependency
used across list endpoints (PRD Ch16.2).
"""

from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int
    pageSize: int


def pagination_params(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, pageSize=pageSize)
