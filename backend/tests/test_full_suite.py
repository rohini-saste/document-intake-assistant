import pytest
from app.models.schema import IntakeState
from app.services.mock_llm import MockLLMProvider
from app.services.state_manager import StateManager
from app.services.document_generator import DocumentGenerator

def test_full_conversational_workflow():
    llm = MockLLMProvider()
    manager = StateManager()
    doc_gen = DocumentGenerator()

    # Step 0: Initial State
    state = IntakeState()
    assert manager.get_next_question(state) == "Could you please provide your full name?"

    # Step 1: User provides Name
    ext, _ = llm.extract_and_respond("Rohini Sharad Saste", state)
    assert ext.full_name == "Rohini Sharad Saste"
    state = manager.merge_state(state, ext)
    assert state.full_name == "Rohini Sharad Saste"
    assert manager.get_next_question(state) == "What is your home address?"

    # Step 2: User provides single-word city address
    ext, _ = llm.extract_and_respond("pune", state)
    assert ext.home_address == "Pune"
    state = manager.merge_state(state, ext)
    assert state.home_address == "Pune"
    assert manager.get_next_question(state) == "Does this document need to cover worldwide assets, or just domestic?"

    # Step 3: User specifies scope
    ext, _ = llm.extract_and_respond("just domestic", state)
    assert ext.covers_worldwide_assets is False
    state = manager.merge_state(state, ext)
    assert state.covers_worldwide_assets is False
    assert manager.get_next_question(state) == "Do you have any children?"

    # Step 4: User specifies children with names in one go
    ext, _ = llm.extract_and_respond("I have two children: Aryan and Ananya", state)
    assert ext.has_children is True
    assert ext.children_names == ["Aryan", "Ananya"]
    state = manager.merge_state(state, ext)
    assert state.has_children is True
    assert state.children_names == ["Aryan", "Ananya"]
    assert manager.get_next_question(state) == "Who would you like to appoint as your executor?"

    # Step 5: User provides executor name and relationship in one go
    ext, _ = llm.extract_and_respond("My brother Ramesh is my executor", state)
    assert ext.executor_name == "Ramesh"
    assert ext.executor_relationship == "Brother"
    state = manager.merge_state(state, ext)
    assert state.executor.name == "Ramesh"
    assert state.executor.relationship == "Brother"
    assert manager.get_next_question(state) == "Who would you like to appoint as your secondary or backup executor? (You can say 'None' if you don't want one)"

    # Step 5b: User skips backup executor
    ext, _ = llm.extract_and_respond("None", state)
    assert ext.backup_executor_name == "None"
    state = manager.merge_state(state, ext)
    assert state.backup_executor.name == "None"
    assert manager.get_next_question(state) == "Are there any specific gifts you would like to leave to anyone?"

    # Step 6: User provides specific gifts
    ext, _ = llm.extract_and_respond("Gold watch to my nephew", state)
    assert ext.specific_gifts == "Gold watch to my nephew"
    state = manager.merge_state(state, ext)
    assert state.specific_gifts == "Gold watch to my nephew"
    assert manager.get_next_question(state) == "Do you have any additional wishes to include?"

    # Step 7: User provides additional wishes
    ext, _ = llm.extract_and_respond("None", state)
    assert ext.additional_wishes == "None"
    state = manager.merge_state(state, ext)
    assert state.additional_wishes == "None"
    assert "gathered all the necessary information" in manager.get_next_question(state)

    # Step 8: Document Generation & Legal Disclaimers
    doc = doc_gen.generate(state)
    assert "FICTIONAL DRAFT - NOT LEGAL ADVICE" in doc
    assert "Rohini Sharad Saste" in doc
    assert "Pune" in doc
    assert "Domestic Assets Only" in doc
    assert "Aryan, Ananya" in doc
    assert "Ramesh" in doc
    assert "Brother" in doc
    assert "Gold watch to my nephew" in doc

    # Step 9: User Correction Flow (Overriding previous facts)
    ext_corr, _ = llm.extract_and_respond("Actually change my name to Rohini Sharma", state)
    state = manager.merge_state(state, ext_corr)
    assert state.full_name == "Rohini Sharma"

    ext_corr2, _ = llm.extract_and_respond("Executor is Sarah (Sister)", state)
    state = manager.merge_state(state, ext_corr2)
    assert state.executor.name == "Sarah"
    assert state.executor.relationship == "Sister"

    updated_doc = doc_gen.generate(state)
    assert "Rohini Sharma" in updated_doc
    assert "Sarah" in updated_doc
    assert "Sister" in updated_doc
