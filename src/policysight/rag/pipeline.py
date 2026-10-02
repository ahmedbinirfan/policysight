from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    roles: tuple[str, ...]


def _parse_roles(raw: str) -> tuple[str, ...]:
    for line in raw.splitlines():
        if line.startswith("roles:"):
            value = line.split(":", 1)[1].strip()
            return tuple(r.strip() for r in value.strip("[]").split(",") if r.strip())
    return ("admin", "staff", "contractor")


def _chunk_text(doc_id: str, body: str, size: int = 400) -> List[Chunk]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    chunks: List[Chunk] = []
    buf: List[str] = []
    n = 0
    for para in paras:
        buf.append(para)
        joined = "\n\n".join(buf)
        if len(joined) >= size:
            n += 1
            chunks.append(Chunk(f"{doc_id}#c{n}", doc_id, joined, ()))
            buf = []
    if buf:
        n += 1
        chunks.append(Chunk(f"{doc_id}#c{n}", doc_id, "\n\n".join(buf), ()))
    return chunks


def load_corpus(corpus_dir: Path) -> List[Chunk]:
    out: List[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        m = FRONT_MATTER.match(raw)
        if m:
            roles = _parse_roles(m.group(1))
            body = m.group(2)
        else:
            roles = ("admin", "staff", "contractor")
            body = raw
        for ch in _chunk_text(path.stem, body):
            out.append(Chunk(ch.chunk_id, ch.doc_id, ch.text, roles))
    return out


def corpus_hash(chunks: Sequence[Chunk]) -> str:
    h = hashlib.sha256()
    for c in sorted(chunks, key=lambda x: x.chunk_id):
        h.update(c.chunk_id.encode())
        h.update(c.text.encode())
        h.update(",".join(c.roles).encode())
    return h.hexdigest()[:16]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score_chunk(query_tokens: Sequence[str], chunk: Chunk) -> float:
    if not query_tokens:
        return 0.0
    bag = set(tokenize(chunk.text))
    hits = sum(1 for t in query_tokens if t in bag)
    return hits / len(query_tokens)


def retrieve(
    question: str,
    role: str,
    chunks: Sequence[Chunk],
    top_k: int = 5,
) -> List[tuple[Chunk, float]]:
    """Sparse keyword retrieve with RBAC filter. Dense/rerank come next."""
    allowed = [c for c in chunks if role in c.roles]
    q = tokenize(question)
    scored = [(c, score_chunk(q, c)) for c in allowed]
    scored = [(c, s) for c, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def support_score(question: str, candidates: Sequence[tuple[Chunk, float]]) -> float:
    if not candidates:
        return 0.0
    return max(s for _, s in candidates)


def answer_from_spans(
    question: str,
    candidates: Sequence[tuple[Chunk, float]],
    floor: float,
) -> Dict:
    """Cite-or-refuse stub: no LLM — answer is the best span if above floor."""
    support = support_score(question, candidates)
    if support < floor or not candidates:
        return {
            "answer": None,
            "refused": True,
            "refuse_reason": "Not in corpus (support below floor)",
            "citations": [],
            "support_score": support,
            "model_route": "stub-refuse",
        }
    best, score = candidates[0]
    quote = best.text[:280] + ("…" if len(best.text) > 280 else "")
    return {
        "answer": quote,
        "refused": False,
        "refuse_reason": None,
        "citations": [
            {
                "chunk_id": best.chunk_id,
                "doc_id": best.doc_id,
                "quote": quote,
            }
        ],
        "support_score": score,
        "model_route": "stub-span",
    }
