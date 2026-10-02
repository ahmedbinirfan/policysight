"""Release gate: frozen golden Q&A. Exit non-zero if metrics miss thresholds.

ponytail: keyword retrieve + span stub only; dense/rerank + LLM faithfulness next.
Ceiling: no dense/rerank yet — upgrade when hybrid lands.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `python -m policysight.eval.run_eval` without install
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from policysight.config import settings
from policysight.rag.pipeline import answer_from_spans, load_corpus, retrieve


def main() -> int:
    chunks = load_corpus(settings.corpus_dir)
    cases = json.loads(settings.golden_path.read_text(encoding="utf-8"))

    retrieval_hits = 0
    refuse_ok = 0
    leak_fails = 0
    n = len(cases)

    print(f"PolicySight eval — {n} cases, {len(chunks)} chunks\n")

    for case in cases:
        q = case["question"]
        role = case["role"]
        expect_refuse = case.get("expect_refuse", False)
        must_doc = case.get("must_retrieve_doc")
        forbid_docs = case.get("forbid_docs") or []

        hits = retrieve(q, role, chunks)
        result = answer_from_spans(q, hits, settings.support_floor)
        hit_docs = {c.doc_id for c, _ in hits}

        retrieved_ok = (must_doc is None) or (must_doc in hit_docs)
        if retrieved_ok and not expect_refuse:
            retrieval_hits += 1

        refuse_match = result["refused"] == expect_refuse
        if refuse_match and expect_refuse:
            refuse_ok += 1
        elif refuse_match and not expect_refuse and result["refused"] is False:
            refuse_ok += 1  # answered when should answer — counted below via retrieval

        leaked = hit_docs.intersection(forbid_docs)
        if leaked:
            leak_fails += 1

        status = "ok" if retrieved_ok and not leaked and (result["refused"] == expect_refuse) else "FAIL"
        print(
            f"[{status}] role={role} refuse={result['refused']} "
            f"support={result['support_score']:.2f} docs={sorted(hit_docs)} — {q[:60]}"
        )

    answerable = [c for c in cases if not c.get("expect_refuse")]
    refuse_cases = [c for c in cases if c.get("expect_refuse")]
    hit_rate = retrieval_hits / max(len(answerable), 1)
    refuse_rate = refuse_ok / max(len(refuse_cases), 1) if refuse_cases else 1.0

    # Scaffold thresholds — raise as hybrid/LLM lands
    min_hit = 0.6
    max_leaks = 0

    print(
        f"\nmetrics: retrieval_hit={hit_rate:.2f} (need ≥{min_hit}) "
        f"leaks={leak_fails} (need {max_leaks}) refuse_cases_ok={refuse_rate:.2f}"
    )

    if hit_rate < min_hit or leak_fails > max_leaks:
        print("GATE FAILED — do not promote this bundle.")
        return 1

    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
