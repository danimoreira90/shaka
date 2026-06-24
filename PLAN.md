# PLAN.md — shaka

**Status:** Sprint 0 (active)
**Read first:** `CLAUDE.md`, `CONTEXT.md`, `KICKOFF.md`.

The executable task list. Each task is one RED→GREEN→REFACTOR cycle. Tasks are
ordered by dependency — do them top to bottom.

---

## Sprint 0 — architecture proof (zero AWS, zero cost)

**Goal.** A thin vertical slice through the whole hexagon using only `local`
adapters: ingest a plain-text document → chunk → embed (deterministic local) →
store in an in-memory vector index. Ask a question → retrieve top-k → return an
**Answer that carries a Citation, or says the library lacks the answer** (HR-5).
Every port call logs a row to the local audit DB.

**Done when (exit criteria):**
- `uv run pytest` green; `uv run pyright` clean (strict); `uv run ruff check` clean.
- `uv run shaka ingest sample.txt` then `uv run shaka ask "..."` returns a grounded
  Answer with a Citation; an absent question returns "not in your library".
- No `boto3` import anywhere outside `adapters/aws/` (there is none yet).
- Audit DB has one row per port call, content-free (hashes only).

---

## Standing rules for CC (apply to every task below)

> You are CC, the coder on shaka. Before coding, read `CLAUDE.md`, `CONTEXT.md`,
> `KICKOFF.md`. Obey all Hard Rules. Specifically:
> - **Never run git** (HR-1). Stage nothing.
> - **TDD:** write the failing test first, show me the RED run, then write the
>   minimum code to pass, then refactor. Don't write code before the test.
> - **Never edit an existing test** to go green (HR-4). Fix production code.
> - `domain/` and `app/` must not import boto3 (HR-8). Sprint 0 uses no AWS at all.
> - Use the canonical names from `CONTEXT.md`.
> - After the task: run `uv run pytest`, `uv run ruff check`, `uv run pyright`, and
>   paste the **full real output** plus `git diff --stat`. Then stop.

---

## Dependency order

```
0.1 models ─▶ 0.2 ports ─▶ 0.3 chunker ─┐
                          ├─ 0.4 embedder ─┤
                          └─ 0.5 vectorindex ─┤
0.7 audit DB (independent) ─────────────────┤
                                            ├─▶ 0.8 ingestion ─▶ 0.9 query ─▶ 0.10 cli ─▶ 0.11 gate
                            0.6 generator ──┘
```

---

### Task 0.1 — Domain models
**Files:** `src/shaka/domain/models.py`, `tests/test_models.py`
**Goal:** pydantic v2 models: `Document`, `Chunk`, `Embedding`, `Query`, `Answer`,
`Citation`. Encode the HR-5 contract in the type.

**RED test spec:**
- `Citation(doc_id, position, snippet)` constructs.
- `Answer(found=True, text="x", citations=[])` **raises** (grounded answer needs ≥1
  citation).
- `Answer(found=False, text="not in your library", citations=[])` is valid.
- `Document` computes a stable `doc_id` from its bytes/text (same text → same id).

**CC prompt:**
> Implement Task 0.1 from `PLAN.md`. Write `tests/test_models.py` first covering the
> four cases listed, show the RED run, then implement `src/shaka/domain/models.py`
> with pydantic v2. `Answer` must reject `found=True` with empty citations via a
> validator. Keep models pure data — no logic beyond validation and `doc_id` hashing.

**Commit:** `test: domain model invariants` → `feat: domain models with HR-5 answer contract`

---

### Task 0.2 — Ports
**Files:** `src/shaka/domain/ports.py` (no test — interfaces)
**Goal:** `typing.Protocol` for `Chunker`, `Embedder`, `VectorIndex`, `Generator`.
One method each. (DocStore, TextExtractor, Retriever, Guardrail arrive in later sprints.)

**CC prompt:**
> Implement Task 0.2: define Protocols in `src/shaka/domain/ports.py` for Chunker
> (`chunk(text, doc_id) -> list[Chunk]`), Embedder (`embed(text) -> Embedding`),
> VectorIndex (`add(chunk, emb) -> None`; `search(query_emb, k) -> list[Chunk]`),
> Generator (`generate(question, chunks) -> Answer`). No implementations. pyright
> strict must pass. No git.

**Commit:** `feat: domain ports (Chunker, Embedder, VectorIndex, Generator)`

---

### Task 0.3 — Local Chunker
**Files:** `src/shaka/adapters/local/chunker.py`, `tests/test_chunker.py`
**Goal:** split text into chunks by size + overlap (from `config`). Deterministic.

**RED test spec:** known text → expected chunk count; overlap present between
consecutive chunks; each Chunk carries `doc_id` and a position; empty text → no chunks.

**CC prompt:**
> Implement Task 0.3 TDD. `tests/test_chunker.py` first (size, overlap, positions,
> empty). Show RED. Then `LocalChunker` in `adapters/local/chunker.py` satisfying the
> Chunker port. Size/overlap come from `shaka.config` (add constants there).

**Commit:** `test: local chunker` → `feat: local chunker (size+overlap)`

---

### Task 0.4 — Local Embedder (deterministic)
**Files:** `src/shaka/adapters/local/embedder.py`, `tests/test_embedder.py`
**Goal:** text → fixed-dim vector, deterministic (hash-seeded). No AWS, no model.

**RED test spec:** same text → identical vector; different text → different vector;
vector length == `config.EMBED_DIM`.

**CC prompt:**
> Implement Task 0.4 TDD. Deterministic local embedder: hash the text to seed a RNG,
> produce a fixed-length float vector (`config.EMBED_DIM`, e.g. 64). Test determinism,
> dimension, and that distinct texts differ. Satisfies the Embedder port.

**Commit:** `test: local embedder` → `feat: deterministic local embedder`

---

### Task 0.5 — Local VectorIndex (in-memory)
**Files:** `src/shaka/adapters/local/vector_index.py`, `tests/test_vector_index.py`
**Goal:** hold (chunk, embedding) pairs; `search` returns top-k by cosine similarity.

**RED test spec:** add three chunks; a query vector near one returns it first; `k`
caps results; empty index returns `[]`.

**CC prompt:**
> Implement Task 0.5 TDD. In-memory VectorIndex: `add` stores chunk+embedding;
> `search(query_emb, k)` returns the k nearest chunks by cosine similarity. Pure
> Python/stdlib math (no numpy needed for Sprint 0). Test nearest-first, k cap, empty.

**Commit:** `test: local vector index` → `feat: in-memory vector index (cosine top-k)`

---

### Task 0.6 — Local Generator (dumb, grounded)
**Files:** `src/shaka/adapters/local/generator.py`, `tests/test_generator.py`
**Goal:** question + retrieved chunks → Answer. No FM. Proves the HR-5 contract.

**RED test spec:** empty chunks → `Answer(found=False, "...not in your library...",
citations=[])`; non-empty chunks → `Answer(found=True, ...)` with ≥1 Citation pointing
at the top chunk.

**CC prompt:**
> Implement Task 0.6 TDD. `LocalGenerator.generate(question, chunks)`: if no chunks,
> return a not-found Answer; else return a grounded Answer whose text is built from the
> top chunk and whose `citations` reference that chunk's doc_id + position. No external
> calls — this is the dumb local stand-in for the Bedrock generator. Enforce HR-5.

**Commit:** `test: local generator grounding` → `feat: dumb grounded local generator`

---

### Task 0.7 — Audit DB + first migration
**Files:** `src/shaka/audit/db.py`, `migrations/0001_init.sql`, `tests/test_audit.py`
**Goal:** local SQLite. `schema_migrations` (with SHA-256, HR-3) + `service_calls`.
`record(service, input, output, cost_usd, latency_ms)` stores **hashes, never content**
(HR-6).

**RED test spec:** applying `0001_init.sql` creates tables; re-applying is a no-op
(SHA match); `record(...)` inserts one row whose stored input/output are hashes, not
the raw strings; `cost_usd` defaults to 0 for local calls.

**CC prompt:**
> Implement Task 0.7 TDD. SQLite audit DB. Migration runner reads `migrations/*.sql`
> in order, stores each file's SHA-256 in `schema_migrations`, refuses to re-apply or
> to run a changed-but-already-applied file (HR-3). `service_calls` columns: id,
> service, input_hash, output_hash, cost_usd, latency_ms, created_at. `record()`
> hashes inputs/outputs (HR-6 — never store content). Test apply, idempotency, and
> content-free recording.

**Commit:** `test: audit db + migration` → `feat: local audit db (content-free, immutable migrations)`

---

### Task 0.8 — Ingestion pipeline
**Files:** `src/shaka/app/ingestion.py`, `tests/test_ingestion.py`
**Goal:** `ingest(text, source, *, chunker, embedder, index, audit) -> IngestionRun`.
Idempotent by `doc_id`. Logs an audit row per embed.

**RED test spec:** ingesting a doc populates the index with the right chunk count;
ingesting the same text twice skips the second (idempotent); an audit row exists per
embedded chunk.

**CC prompt:**
> Implement Task 0.8 TDD against the `local` adapters from 0.3–0.5 and the audit DB
> from 0.7. `app/ingestion.py` orchestrates extract(skip — text given)→chunk→embed→
> index, skipping if `doc_id` already ingested. No boto3 (HR-8). Test population,
> idempotency, audit logging.

**Commit:** `test: ingestion pipeline` → `feat: local ingestion pipeline (idempotent)`

---

### Task 0.9 — Query path
**Files:** `src/shaka/app/query.py`, `tests/test_query.py`
**Goal:** `answer(question, *, embedder, index, generator, audit) -> Answer`.
End-to-end grounded answer.

**RED test spec:** ingest a doc, ask a question answerable from it → `found=True` with
a Citation to the right doc; ask an unrelated question → `found=False`; an audit row
is logged for the query.

**CC prompt:**
> Implement Task 0.9 TDD. `app/query.py`: embed question → `index.search(k)` →
> `generator.generate` → Answer; log an audit row. Write an end-to-end test that
> ingests a small doc via Task 0.8 then asks a present and an absent question. Assert
> the HR-5 contract holds both ways. No boto3.

**Commit:** `test: query path end-to-end` → `feat: local query path (grounded)`

---

### Task 0.10 — Config + composition root + CLI
**Files:** `src/shaka/config.py`, `src/shaka/cli.py`, `tests/test_cli_smoke.py`,
`sample.txt`
**Goal:** `config.py` (chunk size/overlap, EMBED_DIM, default backend `"local"`, cost
caps as constants for later). `cli.py` wires the `local` backend and exposes
`shaka ingest <file>` and `shaka ask "<question>"`.

**RED test spec (smoke):** calling the CLI's `ask` after `ingest` on `sample.txt`
returns an Answer with a Citation; backend defaults to `local`.

**CC prompt:**
> Implement Task 0.10 TDD. `config.py` holds knobs + cost-cap constants (unused for
> now). `cli.py` is the composition root: a `build("local")` that constructs the local
> adapters + audit DB and wires the two pipelines; subcommands `ingest` and `ask`.
> Add a tiny `sample.txt`. Smoke-test that `ingest` then `ask` yields a grounded
> Answer. Wire `shaka = "shaka.cli:main"` in pyproject if needed (tell me — I edit
> pyproject, HR-1 boundary is git not files, but confirm the entry point).

**Commit:** `test: cli smoke` → `feat: config + cli composition root (local backend)`

---

### Task 0.11 — Quality gate (no new code)
**Goal:** prove the exit criteria.

**CC prompt:**
> Run, and paste full output: `uv run pytest -q`, `uv run ruff check`,
> `uv run pyright`. Confirm no `boto3` import exists outside `adapters/aws/`
> (`grep -r "import boto3" src` — should only ever be under aws/, currently none).
> If anything is red, fix production code (never tests) and re-run. Commit nothing.

**Then you (human):** tag the milestone.
```powershell
git add .
git commit -m "chore: Sprint 0 complete — local RAG spine green"
git push
git tag sprint-0 ; git push --tags
```

---

## Evals note (Sprint 0)

Sprint 0 has no FM, so behaviour is deterministic and covered by unit tests — no
`pass@3` needed yet. The HR-5 citation contract is enforced by tests 0.1, 0.6, 0.9.
Real EDD (`pass@3 ≥ 0.90`, regression `pass^3 = 1.00`) begins Sprint 2 when the
Bedrock generator makes answers non-deterministic. `evals/` stays empty until then.

---

## Next sprints (headlines only — detailed when we get there)

- **Sprint 1** — S3 + Textract ingestion; PDF/epub extraction; embeddings still local.
- **Sprint 2** — Bedrock Converse generator + Guardrails; EDD kicks in; real grounding.
- **Sprint 3** — managed path: Bedrock Knowledge Bases / OpenSearch (the paid sprint; tear down after).
- **Sprint 4** — digest pipeline: Comprehend, Translate, Polly.
- **Sprint 5** — lit-review agent: Bedrock Agents / AgentCore / Strands.
- **Threaded throughout** — Macie, CloudTrail, Config, IAM, KMS; A2I; Clarify/Model Cards.
