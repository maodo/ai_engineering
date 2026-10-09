import json
import logging
import uuid

from openai import OpenAI, OpenAIError

from settings import Settings
from tools import RegistryTool

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM API call fails or returns an unusable response."""


class LLMEngine:
    """Chat engine that keeps conversation history and runs a tool-calling loop."""

    def __init__(self, tool_registry: RegistryTool, session_id: str | None = None) -> None:
        settings = Settings()
        self.session_id = session_id or f"ses_{uuid.uuid4().hex}"
        self.client = OpenAI(
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

    def run(self, user_input: str) -> str:
        """Append the user turn to history, then loop until the model
        produces a final text reply (executing requested tools along the way)."""
        self.messages.append({"role": "user", "content": user_input})
        iterations = 0
        while iterations < self.max_iterations:
            iterations += 1

            try:
                response = self.client.chat.completions.create(
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

            # No tool calls -> this is the final reply.
            if not call_result.tool_calls:
                reply = call_result.content
                if not reply:
                    raise LLMError("LLM returned an empty response")
                return reply

            for tool_call in call_result.tool_calls:
                tool_result = self.registry.execute_tool(
                    tool_name=tool_call.function.name,
                    tool_call_id=tool_call.id,
                    arguments=tool_call.function.arguments,
                )
                self.messages.append(tool_result)

        raise LLMError(f"Agent loop hit max iterations ({self.max_iterations}) without a final reply")

    def _assistant_message(self, message) -> dict:
        """Convert the SDK message object into the dict shape the API expects
        when replaying an assistant turn's tool calls back in history."""
        msg = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            msg["tool_calls"] = [tc.model_dump() for tc in message.tool_calls]
        return msg

    @staticmethod
    def _parse_arguments(raw: str) -> dict:
        try:
            args = json.loads(raw)
        except json.JSONDecodeError as e:
            raise LLMError(f"Model returned malformed tool arguments: {e}") from e
        if not isinstance(args, dict):
            raise LLMError("Model tool arguments must be a JSON object")
        return args
