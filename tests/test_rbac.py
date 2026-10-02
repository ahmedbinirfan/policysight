from pathlib import Path

from policysight.config import settings
from policysight.rag.pipeline import load_corpus, retrieve


def test_corpus_loads():
    chunks = load_corpus(settings.corpus_dir)
    assert len(chunks) >= 3
    docs = {c.doc_id for c in chunks}
    assert "leave-policy" in docs
    assert "it-security" in docs


def test_staff_cannot_retrieve_admin_security():
    chunks = load_corpus(settings.corpus_dir)
    hits = retrieve(
        "Who can get production Kubernetes kubeconfig access?",
        "staff",
        chunks,
    )
    assert all(c.doc_id != "it-security" for c, _ in hits)


def test_admin_can_retrieve_security():
    chunks = load_corpus(settings.corpus_dir)
    hits = retrieve(
        "Who can get production Kubernetes kubeconfig access?",
        "admin",
        chunks,
    )
    assert any(c.doc_id == "it-security" for c, _ in hits)


def test_golden_file_exists():
    assert Path(settings.golden_path).is_file()
