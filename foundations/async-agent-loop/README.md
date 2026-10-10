# Async Agent Loop

The async sibling of `foundations/agent_loop`: the same tool-calling agent
loop, but every awaitable seam is actually awaited — so when the model emits
several tool calls in one response, they **run in parallel**.

*Concept: async agent design — model calls are inherently sequential, sibling
tool calls are inherently parallel; the event loop is what enforces that
granularity for free.*

## What actually runs in parallel (and what must not)

```
turn 1                        turn 2 (next model call waits for results)
├─ model call (await, serial) ─┐
│                              ▼
├─ tool A  ┐                   model call (await)
│          ├── asyncio.gather -> parallel
├─ tool B  │                   ├── tool X ┐ gather -> parallel
├─ tool C  ┘                   │   tool Y ┘
│                              ...
└─ history keeps ORIGINAL call order (gather preserves order)
```

- **Parallel:** tool calls *within one response* — the model emitted them
  together, so they are independent by construction.
- **Serial:** model calls *across responses* — the next request contains the
  previous tools' results, so it literally cannot start early.

## Project layout

```
./  (this folder: foundations/async-agent-loop/)
├── main.py       # asyncio REPL: input() offloaded to a thread
├── engine.py     # AsyncLLMEngine: AsyncOpenAI client + parallel tool batch
├── settings.py   # Config loaded from a local .env via pydantic-settings
├── file.txt      # Sample file for manual testing
└── tools/
    ├── base.py       # BaseTool: async `execute()` abstractmethod
    ├── registry.py   # RegistryTool: async execute_tool, errors as data
    ├── read_file/    # blocking file I/O via asyncio.to_thread
    ├── write_file/   # blocking file I/O via asyncio.to_thread
    └── bash/         # TRUE async subprocess (create_subprocess_shell),
                     # denylist guard, timeout via asyncio.wait_for+kill,
                     # decode bytes with errors="replace"
```

## The one platform quirk the code had to absorb

`subprocess.run(..., text=True)` works, but
`asyncio.create_subprocess_shell(..., text=True)` raises
`ValueError("text must be False")` on CPython/ProactorEventLoop. The bash tool
therefore collects raw bytes and decodes them itself
(`decode("utf-8", errors="replace")`).

## Setup

Same as the other folders:

```bash
uv sync                    # from the repo root
cp foundations/async-agent-loop/.env.example foundations/async-agent-loop/.env
# then fill in your values (same BASE_URL / API_KEY / DEFAULT_MODEL)
```

## Usage

```bash
# from the repo root
uv run python foundations/async-agent-loop/main.py
```

The isolation benchmark (3 sleeps + 1 read, no model involved):

```
wall time: 2.02s   (sequential would be ~6s)
```

And a real agent turn ("in ONE batch: run ls, run uname -s, read file.txt,
try rm -rf /") produced exactly 3 parallel tool results plus 1 blocked-guard
result in a single model response.

## Design decisions (the "why")

- **`asyncio.gather` per response, not a global queue.** Parallelism is scoped
  to the batch of calls the model emitted together — the correct granularity,
  no bookkeeping needed beyond `extend(history, results)`.
- **Order preservation.** `gather` returns results in input order, so the
  `tool_call_id` pairing in message history stays valid regardless of which
  subprocess finished first.
- **Errors are data, still.** An async tool failing (blocklist, timeout, bad
  args) becomes `{"ok": false, "error": ...}` in the tool message; one failed
  sibling never cancels the batch (gather without exception swallowing for
  registry-level errors).

## Roadmap (for this folder)

- [ ] Streaming: async iteration over `chat.completions.stream`
- [ ] Per-tool concurrency limits (e.g. semaphore for bash)
- [ ] Cancellation: abort an in-flight batch when the user hits Ctrl-C mid-turn
- [ ] Unit tests with a fake async registry
