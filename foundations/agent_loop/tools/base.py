from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    schema: dict[str, Any]

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return its result as a string."""
        raise NotImplementedError("This method has to be implemented")
