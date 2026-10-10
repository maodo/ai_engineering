import asyncio
import os

from ..base import BaseTool
from .schema import WRITE_FILE_TOOL_SCHEMA


class WriteFileTool(BaseTool):
    name = "write_file"
    schema = WRITE_FILE_TOOL_SCHEMA

    async def execute(
        self,
        path: str,
        content: str,
        mode: str = "overwrite",
        create_dirs: bool = False,
    ) -> str:
        """Write or append text content to a file, returning a size summary."""
        if os.path.isdir(path):
            raise ValueError(f"'{path}' is a directory, not a file")
        if mode not in ("overwrite", "append"):
            raise ValueError(f"Invalid mode '{mode}': expected 'overwrite' or 'append'")

        if create_dirs:
            parent = os.path.dirname(os.path.abspath(path))
            try:
                await asyncio.to_thread(os.makedirs, parent, exist_ok=True)
            except OSError as e:
                raise OSError(f"Cannot create parent directories for '{path}': {e}") from e

        try:
            # Blocking file I/O runs in a thread while sibling tool calls execute
            bytes_written = await asyncio.to_thread(self._write_sync, path, content, mode)
        except OSError as e:
            raise OSError(f"Cannot write to file '{path}': {e}") from e

        action = "Appended to" if mode == "append" else "Wrote"
        return f"{action} '{path}' ({bytes_written} bytes)"

    @staticmethod
    def _write_sync(path: str, content: str, mode: str) -> int:
        open_mode = "w" if mode == "overwrite" else "a"
        with open(path, open_mode, encoding="utf-8") as f:
            f.write(content)
        return len(content)
