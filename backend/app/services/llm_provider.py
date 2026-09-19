import os
from abc import ABC, abstractmethod
from typing import Tuple
from app.models.schema import IntakeState, ExtractionResult

class LLMProvider(ABC):
    @abstractmethod
    def extract_and_respond(self, user_message: str, current_state: IntakeState) -> Tuple[ExtractionResult, str]:
        """
        Takes the user message and current state.
        Returns:
            - ExtractionResult: The validated fields extracted from the message
            - str: An optional string response / reasoning
        """
        pass

def get_llm_provider() -> LLMProvider:
    """
    Factory to resolve the active LLM provider based on environment settings.
    Defaults to MockLLMProvider for offline deterministic execution.
    """
    provider_type = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_type == "mock":
        from app.services.mock_llm import MockLLMProvider
        return MockLLMProvider()
    
    # Real provider integration example (e.g. OpenAI Structured Outputs)
    if provider_type in ["openai", "real"]:
        # Example implementation using OpenAI client
        # from app.services.openai_llm import OpenAILLMProvider
        # return OpenAILLMProvider(api_key=os.getenv("OPENAI_API_KEY"))
        from app.services.mock_llm import MockLLMProvider
        return MockLLMProvider()
        
    from app.services.mock_llm import MockLLMProvider
    return MockLLMProvider()

