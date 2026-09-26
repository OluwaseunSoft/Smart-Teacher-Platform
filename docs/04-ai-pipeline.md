# AI Pipeline

All AI access goes through `backend/app/llm/base.py`. Services never import a
provider SDK directly.

## 1. Provider interface

```python
class LLMProvider(ABC):
    name: str

    def complete(self, messages, *, system=None,
                 temperature=0.3, max_tokens=2048) -> str: ...

    def generate_json(self, messages, *, system=None,
                      temperature=0.2, max_tokens=4096) -> Any:
        """Completion constrained to JSON, parsed with a repair retry."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

> Calls are synchronous to match the synchronous SQLAlchemy session model. An
> async variant can be added later for streaming without changing service call
> sites.

Supported backends:

| Provider | Generation | Embeddings | Notes |
|---|---|---|---|
| `openai` | `gpt-4o-mini` default | `text-embedding-3-small` | needs `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-sonnet-latest` | *(not supported)* | pair with another embedder |
| `ollama` | `llama3.1` default | `nomic-embed-text` | fully local, no keys |

`generate_json` strips markdown fences, extracts the first JSON value, and on parse
failure retries once with a strict "return ONLY valid JSON" system message.

## 2. Stage: Ingestion (`services/ingestion.py`)

1. Extract text — `pypdf` for PDFs, direct for text.
2. Normalize whitespace, strip repeated headers/footers heuristically.
3. Chunk — ~900 chars with 150-char overlap, split on sentence boundaries.
4. Embed each chunk (batched). On embedding failure, store chunks with
   `embedding=None` and continue (retrieval falls back to lexical overlap).

## 3. Stage: Structuring (`services/structuring.py`)

Prompt the LLM with the material's table of contents / first N chunks and ask for a
**concept graph**:

```json
{
  "title": "Cell Biology",
  "concepts": [
    { "title": "The Cell Membrane",
      "summary": "Selective barrier...",
      "difficulty": "intro",
      "subconcepts": [ { "title": "Phospholipid bilayer", "summary": "..." } ] }
  ]
}
```

The service flattens this into `Concept` rows, assigning `order_index` and
`parent_id`. Prompt rules enforce: 5–15 top-level concepts, ordered, each with a
one-paragraph summary, difficulty in `{intro, core, advanced}`.

## 4. Stage: Teaching (`services/teaching.py`)

For each concept, retrieve the top-k chunks via cosine similarity on the concept
title+summary, then generate a lesson:

```
System: You are a patient expert teacher. Ground every claim in the provided
        source excerpts. Use plain language, short paragraphs, concrete examples.
        Output GitHub-flavored markdown with headings.
User:   Concept: ...
        Source excerpts: [1] ... [2] ...
        Produce: learning objectives, explanation, worked example, common
        misconception, and a 3-line summary. Return JSON:
        { "title", "objectives": [...], "content_markdown": "..." }
```

`content_markdown` is stored on `Lesson.content`; objectives as JSON.

## 5. Stage: Assessment (`services/assessment.py`)

Given a lesson + its source chunks, generate 3–6 questions mixing `mcq` and `short`
at varied difficulty (1–5). JSON schema:

```json
{ "questions": [
  { "type": "mcq", "prompt": "...", "options": ["A","B","C","D"],
    "answer": "B", "explanation": "...", "difficulty": 2 },
  { "type": "short", "prompt": "...", "answer": "...",
    "explanation": "...", "difficulty": 4 } ] }
```

**Grading:**
- `mcq` — normalized exact match against `answer` (also matches option letter).
- `short` — LLM-as-judge: the model receives the prompt, reference answer, and the
  student's response and returns `{ "correct": bool, "explanation": str }`.

## 6. Stage: Adaptation (`services/adaptive.py`)

Deterministic policy over per-concept mastery (see `docs/02-data-model.md`):

| Mastery | Action | Behavior |
|---|---|---|
| `< 0.4` | `reteach` | regenerate lesson with `simpler=true` |
| `0.4 – 0.8` | `practice` | generate additional questions |
| `> 0.8` | `advance` | move to next unmastered concept |
| none left | `complete` | session finished |

The LLM only phrases the `message`; the decision is computed in Python so it is
testable and predictable.

## 7. Prompt management

Prompts live as constants/templates in `backend/app/prompts/`. Each prompt module
exposes a function returning `(system, user)` strings, keeping prompt text out of
service logic and easy to version.

## 8. Cost & latency controls (MVP)

- Retrieval limits context to top-k (default 5) chunks.
- `max_tokens` capped per stage.
- Structuring runs once per material, not per concept.
- Lessons generated sequentially; a worker/streaming upgrade is on the roadmap.
