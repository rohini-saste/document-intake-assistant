from pydantic import BaseModel, Field
from typing import List, Optional

class ExecutorDetails(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None

class IntakeState(BaseModel):
    full_name: Optional[str] = None
    home_address: Optional[str] = None
    covers_worldwide_assets: Optional[bool] = None
    has_children: Optional[bool] = None
    children_names: Optional[List[str]] = None
    executor: ExecutorDetails = Field(default_factory=ExecutorDetails)
    specific_gifts: Optional[str] = None
    additional_wishes: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    state: IntakeState

class ChatResponse(BaseModel):
    reply: str
    state: IntakeState
    draft_document: str

class ExtractionResult(BaseModel):
    """
    LLM output format for extracting information from the user message
    It explicitly defines values that were mentioned in the current turn.
    """
    full_name: Optional[str] = None
    home_address: Optional[str] = None
    covers_worldwide_assets: Optional[bool] = None
    has_children: Optional[bool] = None
    children_names: Optional[List[str]] = None
    executor_name: Optional[str] = None
    executor_relationship: Optional[str] = None
    specific_gifts: Optional[str] = None
    additional_wishes: Optional[str] = None
    
    # Reasoning field helps the LLM explain its extraction process
    reasoning: Optional[str] = None
