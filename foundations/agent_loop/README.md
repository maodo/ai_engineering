# Agent Loop

A minimal-but-complete **tool-calling agent** built on the OpenAI Python SDK.
The model can decide to run tools (like reading a file), and the engine loops
until the model produces a final answer.

*Concept: the agent loop — how an LLM becomes an agent that can act, not just answer.*

```
User ──► LLMEngine ──► OpenAI chat.completions
              │                │
              │   tool_calls ◄─┘
              ▼
         RegistryTool ──► BaseTool.execute() ──► result
              │
              └── feed `role: "tool"` result back into history and loop ──► final reply
```

## Project layout

```
./  (this folder: foundations/agent_loop/)
├── main.py            # CLI entry point + interactive REPL
├── engine.py          # LLMEngine: API client, history, agent loop
├── settings.py        # Config loaded from .env via pydantic-settings
├── file.txt           # Sample file for manual testing
├── tools/
│   ├── __init__.py    # Public exports of the tools package
│   ├── base.py        # BaseTool: abstract `name`, `schema`, `execute()`
│   ├── registry.py    # RegistryTool: schema lookup + safe tool execution
│   ├── read_file/     # Example tool: read a file (with line ranges)
│   ├── write_file/    # Example tool: create/append/overwrite a file
│   └── bash/          # Example tool: guarded shell command execution
│       ├── schema.py  # JSON schema sent to the API (chat.completions format)
│       └── tool.py    # ReadFileTool implementation
```

## Core concepts

- **`BaseTool`** — to add a tool, subclass and define a class `name`, a
  `schema` dict, and an `execute(**kwargs) -> str` method.
- **`RegistryTool`** — holds tools by name; exposes their flattened schema list
  to the API and wraps execution so the agent loop can never crash on a bad
  tool call.
- **`LLMEngine`** — keeps the full message history (including assistant
  `tool_calls` and their `role: "tool"` results) and loops until the assistant
  replies with plain text or the iteration budget is exhausted.

### Built-in tools

| Tool         | What it does                                                                 |
| ------------ | ---------------------------------------------------------------------------- |
| `read_file`  | Read a file, optionally a specific inclusive 1-indexed line range.           |
| `write_file` | Write or append text to a file, optionally creating parent directories.      |
| `bash`       | Run a shell command and return exit code / stdout / stderr (with guardrails). |

> ⚠️ **`bash` executes arbitrary commands with your user's permissions.** It
> carries a heuristic denylist (`BLOCKED_PATTERNS` in
> `tools/bash/tool.py`) that blocks destructive and
> system-level commands (deletes, privilege escalation, network piping,
> sensitive paths, ...). This absorbs hallucinated tool calls, but it is
> **not a sandbox or a security boundary** — don't run this agent with secrets
> that matter, or run it inside a container.

## Setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/).

```bash
# from this folder (foundations/agent_loop/):
uv sync                     # install dependencies (run from the repo root)
cp .env.example .env        # then fill in your values in .env
```

`.env` values:

| Variable        | Description                            | Example                     |
| --------------- | -------------------------------------- | --------------------------- |
| `BASE_URL`      | OpenAI-compatible endpoint base URL    | `https://api.openai.com/v1` |
| `API_KEY`       | API key (kept as a `SecretStr`)        | `sk-...`                    |
| `DEFAULT_MODEL` | Model identifier to use                | `gpt-4o-mini`               |

The `.env` file is resolved relative to `settings.py`, so the program can be
started from any working directory.

## Usage

```bash
# from the repo root:
uv run python foundations/agent_loop/main.py "Read file foundations/agent_loop/file.txt and translate it to English"

# interactive REPL (from the repo root):
uv run python foundations/agent_loop/main.py
```

Example interactive session:

```
You: Read the file "foundations/agent_loop/file.txt" and translate it to English.
<Response>
The file says "Bonjour comment vas-tu ?" — French for "Hello, how are you?"
</Response>
You: q
```

## Design decisions (the "why")

- **Errors are data, not crashes.** Tool failures (bad JSON arguments from the
  model, unknown tool name, unreadable file) are reported back to the model as
  the tool result (`{"ok": false, "error": ...}`) so it can retry or correct
  itself, while API errors raise `LLMError` for the caller.
- **History replays assistant tool calls explicitly.** Each assistant turn is
  stored as `{"role": "assistant", "content": ..., "tool_calls": [...]}` — the
  dict shape the Chat Completions API expects, keeping `messages` a pure
  `list[dict]` (no SDK objects leakage).
- **Line ranges are inclusive and 1-indexed**, and out-of-range/inverted ranges
  raise instead of silently returning empty strings.

## Roadmap

- [x] Tool calling / agent loop
- [x] `write_file` tool
- [x] `bash` tool (denylist-guarded)
- [ ] Streaming responses
- [ ] Structured session persistence (resume a conversation)
- [ ] Tests (unit tests for the registry + real end-to-end tool loop)
- [ ] Bash allowlist mode (only pre-approved commands, instead of a denylist)
