from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI

from policysight.api.schemas import AskRequest, AskResponse, Candidate, Citation
from policysight.config import settings
from policysight.rag.pipeline import (
    answer_from_spans,
    corpus_hash,
    load_corpus,
    retrieve,
)

app = FastAPI(
    title="PolicySight",
    description="Cite-or-refuse policy Q&A with RBAC and eval gates.",
    version="0.1.0",
)


@lru_cache(maxsize=1)
def _chunks():
    return tuple(load_corpus(settings.corpus_dir))


@app.get("/health")
def health():
    chunks = _chunks()
    return {
        "ok": True,
        "chunks": len(chunks),
        "bundle_hash": corpus_hash(chunks),
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    chunks = _chunks()
    hits = retrieve(req.question, req.role, chunks)
    result = answer_from_spans(req.question, hits, settings.support_floor)
    return AskResponse(
        answer=result["answer"],
        refused=result["refused"],
        refuse_reason=result["refuse_reason"],
        citations=[Citation(**c) for c in result["citations"]],
        candidates=[
            Candidate(
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                score=s,
                text=c.text[:200],
                roles=list(c.roles),
            )
            for c, s in hits
        ],
        model_route=result["model_route"],
        support_score=result["support_score"],
        bundle_hash=corpus_hash(chunks),
    )
