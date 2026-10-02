# PolicySight

Role-scoped answers over policies/SOPs with **citations**, hybrid retrieval quality gates, and model cost routing — not a chatbot-over-PDFs demo.

Public twin of production RAG patterns (Webifex stays private). Portfolio case: [Notion PolicySight](https://app.notion.com/p/3edf4f89999881078d6ae286669cf986).

## What this proves

| Failure | Mechanism |
|---|---|
| Missed chunk | Hybrid retrieve + retrieval-hit metric |
| Ungrounded answer | Support floor + cite-or-refuse |
| Cannot debug | Candidate ids/scores on the response trace |
| Silent prompt regression | Frozen golden set; `make eval` fails vs champion |
| Cost / latency | Cheap→expensive model route (scaffold: stub) |
| Cross-role leak | ACL filters + unauthorized-retrieval tests |

## Quick start

```bash
make install
make run          # http://127.0.0.1:8000/docs
make eval         # release gate — must be allowed to fail
make test
```

Ask:

```bash
curl -s localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question":"How many days of annual leave?","role":"staff"}' | jq
```

## Layout

```
src/policysight/
  api/          FastAPI (/health, /ask, /embed later)
  rag/          ingest · retrieve · generate · rbac · router · bundle
  eval/         frozen golden Q&A gate
data/corpus/    public synthetic policies (ACL roles in front matter)
data/golden/    qa.json — eval set
```

## Ship bar (before portfolio CMS)

- [ ] Hybrid sparse+dense + rerank (scaffold starts keyword/sparse)
- [ ] RBAC: unauthorized cross-role retrieval = 0
- [ ] `make eval` fails when champion metrics drop
- [ ] FastAPI + Docker
- [ ] Cost/latency log per request
- [ ] `/embed?scenario=quick` per portfolio DEMO_CONTRACT
- [ ] Deploy HTTPS → register on ahmedbinirfan.com (embed off until ready)

## Out of scope

GraphRAG theatre. Multi-agent wrappers. Claiming private client query volume.

## License

MIT — synthetic corpus only; no client data.
