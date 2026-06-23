# CONTEXT.md — shaka domain glossary

**Status:** Draft v0.1

The words we use. Variables, functions, file names, prompts, and agent text MUST
use these canonical terms. When you catch yourself using a vague or overloaded
word with CC, stop and add it here. The next session is sharper for it.

---

## Core entities

### Document
One paper, article, or book the user owns. The unit of input. A Document has a
`source` (filename), a `doc_id` (hash of the bytes), raw extracted `text`, and
`metadata` (title, authors, year — best effort). Stored once; never re-extracted
unless the bytes change.

### Chunk
A slice of a Document's text small enough to embed and retrieve. A Chunk knows its
parent `doc_id` and its position (page / offset) so an answer can cite it. Chunking
strategy (size, overlap) is a design knob, not a domain fact — it lives in config.

### Embedding
A vector of numbers representing a Chunk's meaning, produced by an embeddings model
(Bedrock Titan/Nova embed, or a local fake). "Embedding" = the vector. "Embeddings
model" = the thing that makes it. Keep the two words apart.

### Vector Index
The store that holds embeddings and answers "which chunks are nearest this query?".
Two adapters: `local` (FAISS / sqlite-vec, free) and `aws` (OpenSearch Serverless /
Aurora pgvector). Never call it just "the index" — that collides with DB indexes.

### Library
The whole collection of Documents + Chunks + Embeddings for one user. shaka v1 is
single-user; "Library" = everything ingested so far.

### Query
A user question. Goes through the query path: embed the question → retrieve top-k
Chunks → ground the Bedrock model on them → return an Answer.

### Answer
The Bedrock model's grounded reply plus its Citations. Per HR-5, an Answer with a
factual claim and no Citation is a bug.

### Citation
A pointer from a sentence in the Answer back to the Chunk(s) that support it
(`doc_id` + page/offset). The proof that HR-5 held.

### Ingestion Run
One batch pass that turns raw files into Chunks + Embeddings in the Vector Index.
Offline, idempotent (same bytes → same `doc_id` → skip). Separate from the query
path — different cadence, different tests.

### Service Call (audit)
One row in the local audit DB recording a single AWS (or fake) call: which service,
input hash (never content — HR-6), output hash, est. cost USD, latency ms,
timestamp. This is our local CloudTrail and the evidence trail for HR-5/HR-7.

---

## The two quanta

shaka has two separable parts. Keep them apart in code and conversation.

- **Ingestion pipeline** — offline, batch: `extract → chunk → embed → index`.
- **Query path** — online, per-question: `embed → retrieve → ground → generate`.

They share the Vector Index and nothing else.

---

## Ports (the doors; `domain/ports.py`)

The app talks to these shapes, never to AWS directly (HR-8). Each has a `local`
fake and an `aws` adapter.

| Port | Job | local adapter | aws adapter |
|---|---|---|---|
| `DocStore` | hold raw docs + text | on-disk / sqlite | S3 |
| `TextExtractor` | bytes → text | pypdf / local | Textract |
| `Chunker` | text → chunks | pure Python | (same — no AWS) |
| `Embedder` | chunk → vector | hash/stub vector | Bedrock embeddings |
| `VectorIndex` | store + nearest-k | FAISS / sqlite-vec | OpenSearch / Aurora |
| `Retriever` | query → top-k chunks | wraps VectorIndex | wraps VectorIndex |
| `Generator` | chunks + question → answer | template/echo | Bedrock Converse |
| `Guardrail` | block bad in/out | regex stub | Bedrock Guardrails |

Later sprints add: `Transcriber` (Transcribe), `Translator` (Translate),
`Speaker` (Polly), `ImageLabeler` (Rekognition), `Agent` (Bedrock Agents /
AgentCore / Strands).

---

## AWS services — what each does *here*

Plain "this service has this one job in shaka" so we never cargo-cult a service.

| Service | Its job in shaka | Exam domain |
|---|---|---|
| S3 | store original files | 5 |
| Textract | pull text/tables from scanned or messy PDFs | 1, 3 |
| Transcribe | audio (a recorded talk) → text | 1 |
| Comprehend | language, key phrases, entities, PII scan | 1, 4 |
| Translate | non-English paper → English | 1 |
| Polly | summary → audio | 1 |
| Rekognition | label/flag figures and images | 1, 4 |
| Bedrock (Converse) | summarize, compare, answer | 2, 3 |
| Bedrock embeddings | chunk → vector | 2, 3 |
| Bedrock Knowledge Bases | managed RAG (later sprint) | 3 |
| Bedrock Guardrails | block prompt injection / filter output | 4, 5 |
| OpenSearch / Aurora pgvector / RDS PostgreSQL | vector index (managed) | 3 |
| Bedrock Agents / AgentCore / Strands | lit-review agent (later) | 2, 3 |
| A2I | human review of low-confidence extraction | 4 |
| SageMaker Clarify / Model Cards | explainability, model docs | 4 |
| Macie | scan S3 store for PII | 5 |
| CloudTrail / Config | audit + config compliance | 5 |
| IAM / KMS | access control + encryption | 5 |

---

## RAG / AI vocabulary

- **FM (foundation model)** — the big pretrained model. **LLM** is the text kind.
- **RAG** — retrieve relevant chunks, then have the FM answer using only those.
  shaka's whole reason for being.
- **Grounding** — forcing the answer to rest on retrieved chunks. HR-5(b).
- **Hallucination** — the FM stating something with no source. The enemy.
- **Prompt injection** — adversarial text inside a document trying to hijack the
  FM. Real risk here (a PDF can carry hostile instructions). Guardrail's job.
- **top-k** — how many chunks we retrieve per query. Config knob.
- **Token** — Bedrock pricing/length unit. Disambiguate from any future auth token.
- **temperature** — FM randomness knob; low for grounded answers.

---

## System concepts

- **Port / Adapter** — the door and the thing behind it (HR-8). Domain depends on
  ports; adapters depend on AWS. Never the reverse.
- **Composition root** — `cli.py`. The one place that picks `local` vs `aws` and
  wires adapters into the pipelines.
- **Backend** — `local` (free, default, tests) or `aws` (real, gated by a profile +
  cost cap).
- **Cost cap** — per-run and per-day USD ceiling (HR-7). Lives in `config.py`.

---

## Forbidden / overloaded terms

| Avoid | Use instead |
|---|---|
| "Claude" (bare) | **CC** (the coding agent) or **Bedrock model** (runtime FM) |
| "the index" | **Vector Index** (embeddings) vs DB **index** (SQL) — say which |
| "model" alone | **FM / Bedrock model** vs **SageMaker model** vs **embeddings model** |
| "embedding" for the model | **embeddings model** makes an **embedding** (vector) |
| "search" | **retrieval** (vector top-k) vs **Kendra search** vs **OpenSearch** |
| "document" loosely | **Document** (one paper) vs **Chunk** (a slice of one) |
| "agent" early | reserved for the Bedrock agent in the later sprint; not generic code |
| "token" alone | **Bedrock token** (cost/length); flag if an auth token ever appears |
| "the pipeline" | **ingestion pipeline** vs **query path** — they are different quanta |
| "store" alone | **DocStore** (raw docs) vs **Vector Index** vs **audit DB** |

---

## Language

English everywhere — identifiers, schema, docs, prompts, UI. (The user is in
Brazil, but shaka is a personal research/study tool with no PT-BR consumer
surface. Change this rule here if that changes.)

---

## To resolve (open questions)

- [ ] Chunk size + overlap defaults — start with a sane guess (e.g. ~800 tokens,
      ~100 overlap) and tune against real papers.
- [ ] epub handling — extract via a local lib before any AWS step; confirm in Sprint 1.
- [ ] Which Bedrock embeddings + chat model IDs (verify current IDs before wiring;
      they change, and the agentic services are new).
- [ ] Citation granularity — page-level vs sentence-level. Page first; tighten later.
