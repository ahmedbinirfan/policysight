from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["admin", "staff", "contractor"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    role: Role = "staff"


class Candidate(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    text: str
    roles: List[str]


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    quote: str


class AskResponse(BaseModel):
    answer: Optional[str]
    refused: bool
    refuse_reason: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    candidates: List[Candidate] = Field(default_factory=list)
    model_route: str = "stub"
    support_score: float = 0.0
    bundle_hash: str = ""
