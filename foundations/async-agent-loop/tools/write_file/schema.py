WRITE_FILE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Create a new file or write/append content to an existing file at a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path of the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write to the file.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["overwrite", "append"],
                    "default": "overwrite",
                    "description": "Whether to overwrite the file or append to it.",
                },
                "create_dirs": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to create missing parent directories before writing.",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
}
