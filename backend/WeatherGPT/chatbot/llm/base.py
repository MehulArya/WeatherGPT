from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMService(ABC):
    """Interface for language-model calls (query understanding + generation)."""

    @abstractmethod
    def understand_query(self, user_message: str) -> Dict[str, Any]:
        """Extract a structured query {intent, location_name, date_reference, language, weather_parameters}."""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_content: str,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        """Generate a response, optionally as structured output."""
        raise NotImplementedError