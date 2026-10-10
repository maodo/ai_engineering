# Prompt Chaining

The second concept folder: **prompt chaining** — decomposing a task into fixed
subtasks, each handled by a dedicated LLM call, executed in sequence.
*Concept: structure beats autonomy — predictable pipelines of specialist steps
instead of one open-ended call.*

In this mini-project, the chain writes a blog post in four steps:

```
topic
  │
  ▼
[outline step]  ──► outline (title, 5 sections, bullets)
  │
  ▼
[quality gate]  ──► OutlineGate(compliant, feedback)      ◄── loop: revise on rejection
  │        │                                                      (max 3 revisions)
  │ pass   └── fail ──► [revise outline with gate feedback] ──► re-check
  ▼
[writing step]  ──► full blog post
  │
  ▼
[translation]   ──► post in the target language (e.g. French)
```

## Project layout

```
./  (this folder: effective-agents/01-prompt-chaining/)
├── main.py       # CLI entry point + interactive REPL (input: "topic | language")
├── engine.py     # Llm: API client; run() = stateful, step() = one-shot & typed
├── chain.py      # Chainer: the pipeline, the gate, and the revision loop
├── prompt.py     # The four specialist prompts + the judge criteria
└── settings.py   # Config loaded from a local .env via pydantic-settings
```

## Core concepts

- **One prompt per role.** Each chain step gets its own system prompt
  (`OUTLINER_PROMPT`, `WRITER_PROMPT`, ...) describing exactly one job.
  Small, focused prompts are cheaper to test and to revise than one mega-prompt.
- **`step()` is stateless.** Unlike `agent_loop`'s accumulating history, every
  chain step sends a fresh `messages` list — steps deal in *data* (the outline
  text), not in shared conversation context.
- **The gate is a prompt that returns a type.** `check_outline()` uses
  **structured output** — a Pydantic model (`OutlineGate`) is passed as
  `response_format` through the SDK's `parse()` call, so the judge's verdict is
  validated JSON, not strings to scrape. Rejection feedback flows back into the
  outlining step (feedback as data, `errors are data` again).
- **Bounded loops.** The gate can request revisions up to
  `max_outline_revisions` (3), then `ChainError` aborts the chain rather than
  looping forever.

## Setup

From the repo root:

```bash
uv sync                    # install dependencies
cp effective-agents/01-prompt-chaining/.env.example effective-agents/01-prompt-chaining/.env
# then fill in your values
```

`.env` values (resolved relative to `settings.py`, so CWD doesn't matter):

| Variable        | Description                         | Example                     |
| --------------- | ------------------------------------ | --------------------------- |
| `BASE_URL`      | OpenAI-compatible endpoint base URL  | `https://api.openai.com/v1` |
| `API_KEY`       | API key (kept as a `SecretStr`)      | `sk-...`                    |
| `DEFAULT_MODEL` | Model identifier to use              | `gpt-4o-mini`               |

## Usage

```bash
# from the repo root
uv run python effective-agents/01-prompt-chaining/main.py "topic | language"
# interactive
uv run python effective-agents/01-prompt-chaining/main.py
```

Example:

```
You: why the agent loop matters more than the tools | French
<Blog>
(noise: log lines about the gate)
Le titre, les cinq sections, la traduction complète en français...
</Blog>
You: q
```

Design details visible in the logs: each call is logged (`INFO chain: ...`),
the gate verdict appears as `Outline approved after 0 revision(s)` — of
`Gate rejected outline (attempt 1/3): <feedback>` when the outliner had to
revise.

## Design decisions (the "why")

- **Structured output over prompt-hacked JSON.** The judge returns
  `OutlineGate` via the API's `json_schema` response format — the *wire format*
  is the contract, so the prompt carries the criteria (what to check) and the
  Pydantic model carries the shape (how to answer). Validation errors become
  SDK-level errors, not mystery strings.
- **Gate feedback is the revision payload.** A reject returns numbered,
  actionable feedback which the next outliner step receives verbatim — the
  chain self-corrects without a human in the loop.
- **Why not one prompt?** Chaining keeps each step's context small and each
  role testable in isolation; a single "outline, review, write, translate"
  prompt mixes four jobs into one token-expensive call with lower ceiling.

## Roadmap (for this folder)

- [ ] Per-run criteria: `chain(topic, language, criteria=...)` so gate rules are injectable
- [ ] Stand-alone strict mode: raise on the first gate rejection (no revisions) for eval-style runs
- [ ] Typed `OutlineGate` variants: score-based gate (0–10) rather than boolean
- [ ] Unit tests for gate parsing/revision loop with a fake Llm
