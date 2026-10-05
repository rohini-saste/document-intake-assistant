"""
Comprehensive Deployment & Assessment Readiness Test Suite
Verifies all criteria specified in the Wenup Engineering Technical Test.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schema import IntakeState, ExtractionResult, ExecutorDetails
from app.services.mock_llm import MockLLMProvider
from app.services.state_manager import StateManager
from app.services.document_generator import DocumentGenerator
from app.services.llm_provider import get_llm_provider

client = TestClient(app)

# ============================================================================
# 1. ASSESSMENT SCENARIO & FIELDS COVERAGE (Slides 2 & 3)
# ============================================================================
def test_all_required_assessment_fields_collected():
    """
    Verifies that all 9 required fields from the assessment scenario can be 
    captured, represented in IntakeState, and reflected in the draft document.
    """
    state = IntakeState(
        full_name="Rohini Sharad Saste",
        home_address="Pune, Maharashtra",
        covers_worldwide_assets=True,
        has_children=True,
        children_names=["Aryan", "Ananya"],
        executor=ExecutorDetails(name="Ramesh Saste", relationship="Brother"),
        specific_gifts="Vintage wristwatch to Aryan",
        additional_wishes="Organ donation upon death"
    )
    
    # Check all fields exist in model
    assert state.full_name == "Rohini Sharad Saste"
    assert state.home_address == "Pune, Maharashtra"
    assert state.covers_worldwide_assets is True
    assert state.has_children is True
    assert state.children_names == ["Aryan", "Ananya"]
    assert state.executor.name == "Ramesh Saste"
    assert state.executor.relationship == "Brother"
    assert state.specific_gifts == "Vintage wristwatch to Aryan"
    assert state.additional_wishes == "Organ donation upon death"

    # Generate document and verify all fields appear
    doc = DocumentGenerator().generate(state)
    assert "Rohini Sharad Saste" in doc
    assert "Pune, Maharashtra" in doc
    assert "Worldwide Assets" in doc
    assert "Aryan, Ananya" in doc
    assert "Ramesh Saste" in doc
    assert "Brother" in doc
    assert "Vintage wristwatch to Aryan" in doc
    assert "Organ donation upon death" in doc


# ============================================================================
# 2. APPLICATION REQUIREMENTS & STATE CORRECTIONS (Slide 4)
# ============================================================================
def test_state_corrections_and_deep_immutability():
    """
    Tests that a user can correct previously supplied information at any point
    and that prior state representations remain immutable.
    """
    manager = StateManager()
    
    initial = IntakeState(full_name="Jane Smith", home_address="10 Downing St")
    
    # 1. Correct Name
    ext_name_corr = ExtractionResult(full_name="Jane Doe")
    updated_name = manager.merge_state(initial, ext_name_corr)
    assert updated_name.full_name == "Jane Doe"
    assert initial.full_name == "Jane Smith"  # Deep immutability
    
    # 2. Add Executor
    ext_exec = ExtractionResult(executor_name="James Smith", executor_relationship="Brother")
    with_exec = manager.merge_state(updated_name, ext_exec)
    assert with_exec.executor.name == "James Smith"
    assert with_exec.executor.relationship == "Brother"
    
    # 3. Correct Executor to a different person
    ext_exec_corr = ExtractionResult(executor_name="Sarah Smith", executor_relationship="Sister")
    corrected_exec = manager.merge_state(with_exec, ext_exec_corr)
    assert corrected_exec.executor.name == "Sarah Smith"
    assert corrected_exec.executor.relationship == "Sister"
    assert with_exec.executor.name == "James Smith"  # Prior state intact


# ============================================================================
# 3. LLM BEHAVIOUR, AMBIGUITY & MULTI-FIELD HANDLING (Slide 5)
# ============================================================================
def test_multi_field_input_in_single_turn():
    """
    Verifies the assistant can process multiple fields in a single message in any order.
    """
    llm = MockLLMProvider()
    state = IntakeState()
    
    msg = "My name is Arthur Dent, living at 42 Country Lane, Cottington, worldwide assets, no children"
    ext, _ = llm.extract_and_respond(msg, state)
    
    assert ext.full_name == "Arthur Dent"
    assert ext.home_address == "42 Country Lane, Cottington"
    assert ext.covers_worldwide_assets is True
    assert ext.has_children is False
    assert ext.children_names == []

def test_ambiguous_and_missing_answers_trigger_follow_ups():
    """
    Verifies that when an answer is missing or ambiguous, the state manager
    asks the appropriate sensible follow-up question and does not invent facts.
    """
    manager = StateManager()
    
    # Empty state -> ask full name
    state = IntakeState()
    assert manager.get_next_question(state) == "Could you please provide your full name?"
    
    # Name given -> ask address
    state.full_name = "Jane Doe"
    assert manager.get_next_question(state) == "What is your home address?"
    
    # Address given -> ask estate scope
    state.home_address = "Oxford"
    assert manager.get_next_question(state) == "Does this document need to cover worldwide assets, or just domestic?"
    
    # Scope given -> ask children
    state.covers_worldwide_assets = True
    assert manager.get_next_question(state) == "Do you have any children?"
    
    # Has children = True but names missing -> ask children names
    state.has_children = True
    assert manager.get_next_question(state) == "What are the names of your children?"
    
    # Children names given -> ask executor
    state.children_names = ["Leo", "Maya"]
    assert manager.get_next_question(state) == "Who would you like to appoint as your executor?"
    
    # Executor name given but relationship missing -> ask relationship
    state.executor.name = "David"
    assert manager.get_next_question(state) == "What is your relationship to your executor?"
    
    # Executor relationship given -> ask backup executor
    state.executor.relationship = "Friend"
    assert "backup executor" in manager.get_next_question(state).lower()
    
    # Backup Executor name given as None -> ask specific gifts
    state.backup_executor.name = "None"
    assert manager.get_next_question(state) == "Are there any specific gifts you would like to leave to anyone?"
    
    # Specific gifts given -> ask additional wishes
    state.specific_gifts = "None"
    assert manager.get_next_question(state) == "Do you have any additional wishes to include?"
    
    # All confirmed -> completed statement
    state.additional_wishes = "None"
    assert "gathered all the necessary information" in manager.get_next_question(state)

def test_mandatory_legal_disclaimer_in_draft_document():
    """
    Verifies the document is clearly labeled as fictional and not legal advice.
    """
    generator = DocumentGenerator()
    doc = generator.generate(IntakeState())
    assert "DRAFT - PERSONAL WISHES DOCUMENT" in doc
    assert "FICTIONAL DRAFT - NOT LEGAL ADVICE" in doc
    assert "does not constitute a valid legal document" in doc


# ============================================================================
# 4. API CONTRACT, ERROR RESILIENCE & DEPLOYMENT HEALTH (Slides 6 & 7)
# ============================================================================
def test_deployment_health_check_endpoint():
    """
    Verifies health check endpoint returns 200 OK for load balancers / deployment monitoring.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_full_api_conversation_cycle():
    """
    Simulates a full end-to-end API session over HTTP:
    /api/reset -> multiple /api/chat turns -> final completed draft.
    """
    # 1. Reset Session
    res_reset = client.post("/api/reset")
    assert res_reset.status_code == 200
    data = res_reset.json()
    assert "reply" in data
    assert data["state"]["full_name"] is None
    
    state = data["state"]
    
    # 2. Send Name
    res1 = client.post("/api/chat", json={"message": "Rohini Saste", "state": state})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["state"]["full_name"] == "Rohini Saste"
    assert "address" in data1["reply"].lower()
    
    # 3. Send Address
    res2 = client.post("/api/chat", json={"message": "Pune", "state": data1["state"]})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["state"]["home_address"] == "Pune"
    assert "worldwide" in data2["reply"].lower()

def test_api_graceful_error_recovery():
    """
    Verifies that malformed user chat payloads do not crash the API server with an unhandled 500 error.
    """
    # Sending missing state field triggers graceful 422 or handled recovery
    res = client.post("/api/chat", json={"message": "Hello"})
    assert res.status_code == 422  # Handled Pydantic validation error

def test_provider_factory_resolution():
    """
    Verifies the LLM provider factory instantiates a valid LLMProvider implementation.
    """
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)
    ext, _ = provider.extract_and_respond("Jane Doe", IntakeState())
    assert isinstance(ext, ExtractionResult)
