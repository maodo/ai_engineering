import asyncio
import logging
import sys

from engine import AsyncLLMEngine
from tools import RegistryTool, ReadFileTool, WriteFileTool, BashTool

logger = logging.getLogger(__name__)


async def read_input(prompt: str) -> str:
    """input() blocks the thread the event loop is running on; offload it."""
    return await asyncio.to_thread(input, prompt)


async def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    tool_registry = RegistryTool()
    tool_registry.register_all([
        ReadFileTool(),
        WriteFileTool(),
        BashTool(),
    ])
    agent = AsyncLLMEngine(tool_registry=tool_registry)

    print("Async interactive chat (type 'q' or 'exit' to quit)")
    while True:
        try:
            user_input = await read_input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye !")
            return 0
        if user_input in ("q", "exit"):
            print("Bye !")
            return 0
        try:
            response = await agent.run(user_input)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            logger.exception("Agent turn failed")
            continue  # keep the session alive on a bad turn
        print("<Response>")
        print(response)
        print("</Response>")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
