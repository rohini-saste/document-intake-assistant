import json
import os
import pytest
from pydantic import ValidationError
from app.models.schema import IntakeState, ExtractionResult
from app.services.mock_llm import MockLLMProvider
from app.services.state_manager import StateManager
from app.services.document_generator import DocumentGenerator

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), "fixtures.json")

@pytest.fixture
def fixtures_data():
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_fixtures(fixtures_data):
    llm = MockLLMProvider()
    state = IntakeState()
    
    for case in fixtures_data["valid_responses"]:
        extraction, _ = llm.extract_and_respond(case["input"], state)
        for key, expected_val in case["expected_extraction"].items():
            actual_val = getattr(extraction, key)
            assert actual_val == expected_val, f"Failed on '{case['description']}': expected {expected_val} for {key}, got {actual_val}"

def test_ambiguous_fixtures(fixtures_data):
    llm = MockLLMProvider()
    manager = StateManager()
    
    for case in fixtures_data["ambiguous_responses"]:
        state = IntakeState(**case.get("initial_state", {}))
        extraction, _ = llm.extract_and_respond(case["input"], state)
        merged_state = manager.merge_state(state, extraction)
        
        if "expected_unconfirmed" in case:
            for field in case["expected_unconfirmed"]:
                assert getattr(merged_state, field) is None
                
        if "expected_next_question" in case:
            next_q = manager.get_next_question(merged_state)
            assert next_q == case["expected_next_question"]

def test_malformed_model_response_handling(fixtures_data):
    manager = StateManager()
    state = IntakeState()
    
    # Test handling of malformed payloads
    for case in fixtures_data["malformed_responses"]:
        payload = case["payload"]
        if isinstance(payload, dict):
            # Attempting to validate corrupt dict against ExtractionResult should raise ValidationError or fail safely
            with pytest.raises(ValidationError):
                ExtractionResult.model_validate(payload)
        elif isinstance(payload, str):
            # Empty or invalid string parsing
            extraction, _ = MockLLMProvider().extract_and_respond(payload, state)
            assert isinstance(extraction, ExtractionResult)
