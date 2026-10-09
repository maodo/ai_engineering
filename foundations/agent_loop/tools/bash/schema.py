BASH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": (
            "Run a shell command and return its exit code, stdout and stderr. "
            "Useful for listing files (ls), inspecting content, and simple "
            "inspection tasks. Destructive or system-level commands are blocked."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 120,
                    "default": 30,
                    "description": "Seconds to wait for the command before stopping it.",
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
}
