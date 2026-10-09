READ_FILE_TOOL_SCHEMA = {
    "type": "function",
    "function":{
        "name": "read_file",
        "description": "Read the contents of a file at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read.",
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "The character encoding to use when reading the file.",
                },
                "line_start": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Optional starting line number to begin reading from (1-indexed).",
                },
                "line_end": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Optional ending line number to stop reading at.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    }
}
