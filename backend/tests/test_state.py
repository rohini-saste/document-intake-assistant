from app.models.schema import IntakeState, ExtractionResult
from app.services.state_manager import StateManager
from app.services.mock_llm import MockLLMProvider

def test_state_merge():
    manager = StateManager()
    current = IntakeState()
    
    # Simulate extracting full name
    ext1 = ExtractionResult(full_name="Jane Smith")
    current = manager.merge_state(current, ext1)
    
    assert current.full_name == "Jane Smith"
    assert current.home_address is None
    
    # Simulate extracting address and children status
    ext2 = ExtractionResult(home_address="10 Downing St", has_children=True)
    current = manager.merge_state(current, ext2)
    
    assert current.full_name == "Jane Smith"
    assert current.home_address == "10 Downing St"
    assert current.has_children is True
    
    # Simulate correction (overwriting name)
    ext3 = ExtractionResult(full_name="Jane Doe")
    next_state = manager.merge_state(current, ext3)
    
    assert next_state.full_name == "Jane Doe"
    assert current.full_name == "Jane Smith"  # Ensure original state was not mutated

    # Test nested executor update without mutating prior state
    ext4 = ExtractionResult(executor_name="Sarah", executor_relationship="Sister")
    final_state = manager.merge_state(next_state, ext4)
    assert final_state.executor.name == "Sarah"
    assert final_state.executor.relationship == "Sister"
    assert next_state.executor.name is None

def test_mock_llm_heuristics():
    llm = MockLLMProvider()
    state = IntakeState()
    
    # Test Name Extraction
    ext, _ = llm.extract_and_respond("My name is Jane Smith", state)
    assert ext.full_name == "Jane Smith"
    
    # Test multiple fields (executor + relation)
    ext, _ = llm.extract_and_respond("My brother James is my executor", state)
    assert ext.executor_relationship == "Brother"
    assert ext.executor_name == "James"
    
    # Test executor pattern with parentheses
    ext, _ = llm.extract_and_respond("Sarah (Sister)", state)
    assert ext.executor_name == "Sarah"
    assert ext.executor_relationship == "Sister"

    # Test combined kids extraction
    ext, _ = llm.extract_and_respond("I have two kids: Alice and Bob", state)
    assert ext.has_children is True
    assert ext.children_names == ["Alice", "Bob"]

    # Test domestic/worldwide scope
    ext, _ = llm.extract_and_respond("worldwide assets please", state)
    assert ext.covers_worldwide_assets is True

    ext, _ = llm.extract_and_respond("just domestic", state)
    assert ext.covers_worldwide_assets is False
    
    # Test missing fields context
    state.has_children = True
    ext, _ = llm.extract_and_respond("Alice and Bob", state)
    assert ext.children_names == ["Alice", "Bob"]

def test_document_generator():
    from app.services.document_generator import DocumentGenerator
    from app.models.schema import ExecutorDetails
    
    generator = DocumentGenerator()
    state = IntakeState(
        full_name="Jane Doe",
        home_address="123 Maple St",
        covers_worldwide_assets=True,
        has_children=False,
        executor=ExecutorDetails(name="Sarah Doe", relationship="Sister"),
        specific_gifts="Vintage Watch to nephew",
        additional_wishes="Burial at sea"
    )
    
    doc = generator.generate(state)
    assert "Jane Doe" in doc
    assert "123 Maple St" in doc
    assert "Worldwide Assets" in doc
    assert "Children**: None" in doc
    assert "Sarah Doe" in doc
    assert "Sister" in doc
    assert "Vintage Watch to nephew" in doc
    assert "Burial at sea" in doc

def test_api_routes():
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    
    # Test reset endpoint
    res = client.post("/api/reset")
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "state" in data
    assert "draft_document" in data
    
    # Test chat endpoint
    res = client.post("/api/chat", json={
        "message": "My name is John Smith",
        "state": data["state"]
    })
    assert res.status_code == 200
    chat_data = res.json()
    assert chat_data["state"]["full_name"] == "John Smith"

