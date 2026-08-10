"""Global search schemas."""

import uuid

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: uuid.UUID
    type: str  # "patient" | "appointment" | "consultation" | "report" | "user"
    title: str
    subtitle: str | None = None
    href: str


class SearchResultsOut(BaseModel):
    query: str
    results: list[SearchResultItem]
