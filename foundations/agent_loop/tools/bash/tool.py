import re
import subprocess
import textwrap

from ..base import BaseTool
from .schema import BASH_TOOL_SCHEMA

# Best-effort denylist against destructive or sensitive commands (mainly to absorb
# hallucinated tool calls). This is heuristic, NOT a security boundary.
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    (r"\b(rm|rmdir|mkfs(\.\w+)?|dd|shred|truncate|unlink)\b", "destructive filesystem command"),
    (r"\b(shutdown|reboot|halt|poweroff|kill|killall|pkill)\b", "system / process control command"),
    (r"\b(sudo|su|doas|chmod|chown|passwd)\b", "privilege or account command"),
    (r"\b(nc|ncat|netcat|ssh|scp|sftp)\b", "network command"),
    (r"\b(env|printenv|export)\b", "environment leaking command"),
    (r"\bgit\b.*(--force|-f)\b.*\bpush\b|\bgit\b.*\bpush\b.*(--force|-f)\b", "git history rewrite"),
    (r"\bgit\b.*\breset\b.*--hard\b", "git history rewrite"),
    (r"\b(curl|wget)\b.*(\||>>,?>)", "network command piped into the shell or a file"),
    (r">?>\s*/(etc|dev|sys|boot|usr|bin|sbin)/", "redirect toward a sensitive system path"),
    (r"\b(etc|sys_root|\.ssh)/|\$?~?/?\.ssh\b|/etc/shadow\b|/etc/passwd\b", "sensitive path"),
    (r"\bhome\b.*\brm\b|\brm\b.*\bhome\b.*-r", "home deletion pattern"),
    (r"\bmv\b.*/(etc|dev|boot|usr|bin|sbin)\b", "moving critical system files"),
]

MAX_OUTPUT_CHARS = 10_000


class BashTool(BaseTool):
    name = "bash"
    schema = BASH_TOOL_SCHEMA

    def execute(self, command: str, timeout: int = 30) -> str:
        """Run a shell command if it passes the denylist; return exit code, stdout."""
        blocked_reason = self.is_command_blocked(command)
        if blocked_reason:
            raise PermissionError(
                f"Command blocked ({blocked_reason}). It is considered dangerous and will not be executed."
            )

        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Command '{command}' timed out after {timeout} seconds. "
                f"Partial stdout: {e.stdout!r}"
            ) from e
        except OSError as e:
            raise OSError(f"Command '{command}' failed to run: {e}") from e

        return textwrap.dedent(
            f"""\
            exit_code: {process.returncode}
            stdout:
            {self._truncate(process.stdout)}

            stderr:
            {self._truncate(process.stderr)}
            """
        )

    @staticmethod
    def is_command_blocked(command: str) -> str | None:
        """Return a reason string if the command matches a denylisted pattern, else None."""
        normalized = " ".join(command.lower().split())
        for pattern, reason in BLOCKED_PATTERNS:
            if re.search(pattern, normalized, flags=re.MULTILINE):
                return reason
        return None

    @staticmethod
    def _truncate(output: str) -> str:
        if len(output) <= MAX_OUTPUT_CHARS:
            return output
        cut = len(output) - MAX_OUTPUT_CHARS
        return f"{output[:-cut]}\n\n[... output truncated, {cut} chars omitted ...]"
