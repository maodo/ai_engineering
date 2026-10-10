import logging

from pydantic import BaseModel

from engine import Llm, LlmResult
from prompt import (
    OUTLINER_PROMPT,
    OUTLINE_JUDGE_PROMPT,
    WRITER_PROMPT,
    TRANSLATOR_PROMPT,
)

logger = logging.getLogger(__name__)


class ChainError(Exception):
    """Raised when the chain fails or exceeds its revision budget."""


class OutlineGate(BaseModel):
    """Structured verdict of the outline quality gate."""
    compliant: bool
    feedback: str


class Chainer:
    max_outline_revisions = 3

    def __init__(self, agent: Llm) -> None:
        self.agent = agent

    def chain(self, user_input: str, target_language: str) -> LlmResult:
        """Run the chain: outline -> gate -> revise if needed -> blog post -> translation."""
        outline = self.generate_outline(user_input)
        gate = self.check_outline(outline.text)
        attempts = 0
        while not gate.compliant:
            attempts += 1
            if attempts > self.max_outline_revisions:
                raise ChainError(
                    f"Outline failed compliance {attempts - 1} revision(s); last feedback: {gate.feedback}"
                )
            logger.info("Gate rejected outline (attempt %d/%d): %s", attempts, self.max_outline_revisions, gate.feedback)
            outline = self.agent.step(
                OUTLINER_PROMPT,
                f"Revise the outline below so that it satisfies every piece of feedback.\n\n"
                f"Outline:\n{outline.text}\n\nFeedback:\n{gate.feedback}",
            )
            gate = self.check_outline(outline.text)
        logger.info("Outline approved after %d revision(s)", attempts)

        blog_post = self.write_blog_post(outline.text)
        return self.translate_blog_post(blog_post.text, target_language)

    def generate_outline(self, user_input: str) -> LlmResult:
        return self.agent.step(OUTLINER_PROMPT, user_input)

    def check_outline(self, outline: str) -> OutlineGate:
        """Gate: the LLM judges the outline against the criteria and returns
        a validated structured verdict (Pydantic structured output)."""
        return self.agent.step(OUTLINE_JUDGE_PROMPT, outline, output_model=OutlineGate)

    def write_blog_post(self, outline: str) -> LlmResult:
        return self.agent.step(WRITER_PROMPT, outline)

    def translate_blog_post(self, blog_post: str, target_language: str) -> LlmResult:
        return self.agent.step(TRANSLATOR_PROMPT.format(target_language=target_language), blog_post)
