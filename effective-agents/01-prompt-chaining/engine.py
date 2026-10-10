from settings import Settings
from openai import OpenAI, OpenAIError
import uuid
import logging
from pydantic import BaseModel



logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Raised when the LLM API call fails or returns an unusable response."""

class LlmResult(BaseModel):
    text: str


class Llm:
    def __init__(self, session_id: str | None = None) -> None:
        settings = Settings()
        self.session_id = session_id or f"ses_{uuid.uuid4().hex}"
        self.client = OpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key.get_secret_value(),
            default_headers={
                "x-opencode-session": self.session_id,
            },
        )
        self.default_model = settings.default_model
        self.messages = []

    def step(
        self,
        system_prompt: str,
        user_input: str,
        model=None,
        output_model: type[BaseModel] | None = None,
    ) -> LlmResult | BaseModel:
        """One-shot, stateless LLM call used by chains: each step gets a fresh
        message list and no history is accumulated across steps.

        When `output_model` (a Pydantic model) is provided, structured output
        is used and a validated instance of that model is returned."""
        messages = [
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        if output_model is not None:
            try:
                completion = self.client.chat.completions.parse(
                    model=model or self.default_model,
                    messages=messages,
                    response_format=output_model,
                )
            except OpenAIError as e:
                logger.error("LLM structured-output call failed: %s", e)
                raise LLMError(f"LLM API call failed: {e}") from e
            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise LLMError("LLM returned no structured output")
            return parsed

        try:
            completion = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
            )
        except OpenAIError as e:
            logger.error("LLM API call failed: %s", e)
            raise LLMError(f"LLM API call failed: {e}") from e

        reply = completion.choices[0].message.content
        if not reply:
            raise LLMError("LLM returned an empty response")
        return LlmResult(text=reply)
