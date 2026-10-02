"""Release gate: frozen golden Q&A. Exit non-zero if metrics miss thresholds.

ponytail: keyword retrieve + span stub only; dense/rerank + LLM faithfulness next.
Ceiling: no dense/rerank yet — upgrade when hybrid lands.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from policysight.config import settings
from policysight.rag.pipeline import answer_from_spans, load_corpus, retrieve


def main() -> int:
    chunks = load_corpus(settings.corpus_dir)
    cases = json.loads(settings.golden_path.read_text(encoding="utf-8"))

    answerable_ok = 0
    answerable_n = 0
    refuse_ok = 0
    refuse_n = 0
    leak_fails = 0

    print(f"PolicySight eval — {len(cases)} cases, {len(chunks)} chunks\n")

    for case in cases:
        q = case["question"]
        role = case["role"]
        expect_refuse = bool(case.get("expect_refuse", False))
        must_doc = case.get("must_retrieve_doc")
        forbid_docs = case.get("forbid_docs") or []

        hits = retrieve(q, role, chunks)
        result = answer_from_spans(q, hits, settings.support_floor)
        hit_docs = {c.doc_id for c, _ in hits}
        leaked = bool(hit_docs.intersection(forbid_docs))
        if leaked:
            leak_fails += 1

        case_ok = not leaked and (result["refused"] == expect_refuse)
        if expect_refuse:
            refuse_n += 1
            if case_ok:
                refuse_ok += 1
        else:
            answerable_n += 1
            retrieved_ok = must_doc is None or must_doc in hit_docs
            case_ok = case_ok and retrieved_ok and not result["refused"]
            if case_ok:
                answerable_ok += 1

        status = "ok" if case_ok else "FAIL"
        print(
            f"[{status}] role={role} refuse={result['refused']} "
            f"support={result['support_score']:.2f} docs={sorted(hit_docs)} — {q[:60]}"
        )

    hit_rate = answerable_ok / max(answerable_n, 1)
    refuse_rate = refuse_ok / max(refuse_n, 1)

    min_hit = 0.6
    min_refuse = 1.0
    max_leaks = 0

    print(
        f"\nmetrics: answerable_ok={hit_rate:.2f} (need ≥{min_hit}) "
        f"refuse_ok={refuse_rate:.2f} (need ≥{min_refuse}) "
        f"leaks={leak_fails} (need {max_leaks})"
    )

    if hit_rate < min_hit or refuse_rate < min_refuse or leak_fails > max_leaks:
        print("GATE FAILED — do not promote this bundle.")
        return 1

    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
