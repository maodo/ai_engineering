from ..base import BaseTool
from .schema import READ_FILE_TOOL_SCHEMA


class ReadFileTool(BaseTool):
    name = "read_file"
    schema = READ_FILE_TOOL_SCHEMA

    def execute(
        self,
        path: str,
        encoding: str = "utf-8",
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> str:
        """Read the contents of a file, optionally within a 1-indexed line range."""
        if line_end is not None and line_start is not None and line_end < line_start:
            raise ValueError(f"line_end ({line_end}) must be >= line_start ({line_start})")
        if (line_start is not None and line_start < 1) or (line_end is not None and line_end < 1):
            raise ValueError("line_start and line_end must be >= 1 (1-indexed)")

        try:
            with open(path, "r", encoding=encoding) as f:
                if line_start is None and line_end is None:
                    return f.read()
                lines = f.readlines()
                # line ranges are inclusive and 1-indexed
                start = (line_start - 1) if line_start is not None else 0
                end = line_end if line_end is not None else len(lines)
                if start >= len(lines):
                    raise ValueError(f"No such range of lines in file: file has {len(lines)} line(s)")
                return "".join(lines[start:end])
        except OSError as e:
            raise OSError(f"Cannot read file '{path}': {e}") from e
