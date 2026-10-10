# AI Engineering Playground

A monorepo for learning AI engineering concepts, one small folder at a time.

Each folder is a self-contained mini-project: a focused implementation of a
single concept, with its own README covering the idea, the file structure,
how to run it, and the design choices ("the why").

## Concepts

| Folder                   | Concept               | Status |
| ------------------------ | --------------------- | ------ |
| `foundations/agent_loop` | Agent loop: an LLM that calls tools and iterates until it answers | ✅ |
| `effective-agents/01-prompt-chaining` | Prompt chaining: outline → quality gate → write → translate | ✅ |

## Setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
uv sync          # install dependencies (from the repo root)
```

Each mini-project ships its own `.env.example` — copy it to `.env` inside that
project folder and fill in your API credentials. See the project's README for
details.

## Concepts roadmap

- [x] Agent loop with tool calling (`read_file`, `write_file`, guarded `bash`)
- [x] Prompt chaining with a quality gate (outline → check → revise → write → translate)
- [ ] Streaming responses
- [ ] Structured output / schema-driven tool generation
- [ ] RAG basics
- [ ] Evals
