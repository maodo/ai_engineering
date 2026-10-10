import json
import logging
from typing import Any

from .base import BaseTool

logger = logging.getLogger(__name__)


class RegistryTool:
    def __init__(self) -> None:
        self.tools: dict[str, BaseTool] = {}

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema for tool in self.tools.values()]

    def register(self, tool: BaseTool) -> None:
        self.tools[tool.name] = tool

    def register_all(self, tools: list[BaseTool]) -> None:
        for tool in tools:
            self.register(tool)

    async def execute_tool(self, tool_name: str, tool_call_id: str, arguments: str | dict) -> dict:
        """Execute a tool safely and always return a well-formed `role: "tool"`
        message so the API contract holds. Errors are data, not crashes."""
        content = await self._run(tool_name, arguments)
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }

    async def _run(self, tool_name: str, arguments: str | dict) -> str:
        tool = self.tools.get(tool_name)
        if tool is None:
            known = ", ".join(self.tools) or "none"
            return json.dumps({"ok": False, "error": f"Unknown tool '{tool_name}'. Available tools: {known}"})

        try:
            args = arguments if isinstance(arguments, dict) else json.loads(arguments)
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": f"Malformed tool arguments (not valid JSON): {e}"})
        if not isinstance(args, dict):
            return json.dumps({"ok": False, "error": "Tool arguments must be a JSON object"})

        try:
            result = await tool.execute(**args)
            return json.dumps({"ok": True, "result": str(result)})
        except Exception as e:  # tool-level failures go back to the model, keep the agent alive
            logger.warning("Tool '%s' failed: %s", tool_name, e)
            return json.dumps({"ok": False, "error": str(e)})
