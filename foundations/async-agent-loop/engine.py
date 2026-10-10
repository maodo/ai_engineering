import asyncio
import logging
import uuid

from openai import AsyncOpenAI, OpenAIError

from settings import Settings
from tools import RegistryTool

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM API call fails or returns an unusable response."""


class AsyncLLMEngine:
    """Async chat engine that keeps conversation history and runs a
    tool-calling loop where sibling tool calls run in parallel."""

    def __init__(self, tool_registry: RegistryTool, session_id: str | None = None) -> None:
        settings = Settings()
        self.session_id = session_id or f"ses_{uuid.uuid4().hex}"
        self.client = AsyncOpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key.get_secret_value(),
            default_headers={
                "x-opencode-session": self.session_id,
            },
        )
        self.system_prompt = "You are a helpful assistant that answers questions accurately and concisely."
        self.default_model = settings.default_model
        self.max_iterations = 10
        self.registry = tool_registry
        self.messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
        ]

    async def run(self, user_input: str) -> str:
        """Append the user turn to history and loop until the model produces a
        final text reply. Tool calls that arrive together in one response are
        executed in parallel; model calls stay sequential (the next request
        depends on previous tool results)."""
        self.messages.append({"role": "user", "content": user_input})
        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1

            try:
                response = await self.client.chat.completions.create(
                    model=self.default_model,
                    messages=self.messages,
                    tools=self.registry.schemas,
                    tool_choice="auto",
                )
            except OpenAIError as e:
                logger.error("LLM API call failed: %s", e)
                raise LLMError(f"LLM API call failed: {e}") from e

            call_result = response.choices[0].message
            self.messages.append(self._assistant_message(call_result))

            if not call_result.tool_calls:
                reply = call_result.content
                if not reply:
                    raise LLMError("LLM returned an empty response")
                return reply

            # Sibling tool calls are independent by construction (the model
            # emitted them together): run them concurrently. gather() preserves
            # input order, so tool_call_id pairing stays valid in history.
            tool_results = await asyncio.gather(
                *[
                    self.registry.execute_tool(
                        tool_name=tc.function.name,
                        tool_call_id=tc.id,
                        arguments=tc.function.arguments,
                    )
                    for tc in call_result.tool_calls
                ]
            )
            self.messages.extend(tool_results)

        raise LLMError(f"Agent loop hit max iterations ({self.max_iterations}) without a final reply")

    @staticmethod
    def _assistant_message(message) -> dict:
        """Convert the SDK message object into the dict shape the API expects
        when replaying an assistant turn's tool calls back in history."""
        msg = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            msg["tool_calls"] = [tc.model_dump() for tc in message.tool_calls]
        return msg
