import os

from ..base import BaseTool
from .schema import WRITE_FILE_TOOL_SCHEMA


class WriteFileTool(BaseTool):
    name = "write_file"
    schema = WRITE_FILE_TOOL_SCHEMA

    def execute(
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
                os.makedirs(parent, exist_ok=True)
            except OSError as e:
                raise OSError(f"Cannot create parent directories for '{path}': {e}") from e

        open_mode = "w" if mode == "overwrite" else "a"
        try:
            with open(path, open_mode, encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise OSError(f"Cannot write to file '{path}': {e}") from e

        action = "Appended to" if mode == "append" else "Wrote"
        return f"{action} '{path}' ({len(content)} bytes)"
