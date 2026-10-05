from pydantic import BaseModel, Field
from typing import List, Optional

class ExecutorDetails(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    relationship: Optional[str] = Field(default=None, max_length=100)

class IntakeState(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    home_address: Optional[str] = Field(default=None, max_length=500)
    covers_worldwide_assets: Optional[bool] = None
    has_children: Optional[bool] = None
    children_names: Optional[List[str]] = None
    executor: ExecutorDetails = Field(default_factory=ExecutorDetails)
    backup_executor: ExecutorDetails = Field(default_factory=ExecutorDetails)
    specific_gifts: Optional[str] = Field(default=None, max_length=2000)
    additional_wishes: Optional[str] = Field(default=None, max_length=2000)

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
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
    full_name: Optional[str] = Field(default=None, max_length=200)
    home_address: Optional[str] = Field(default=None, max_length=500)
    covers_worldwide_assets: Optional[bool] = None
    has_children: Optional[bool] = None
    children_names: Optional[List[str]] = None
    executor_name: Optional[str] = Field(default=None, max_length=200)
    executor_relationship: Optional[str] = Field(default=None, max_length=100)
    backup_executor_name: Optional[str] = Field(default=None, max_length=200)
    backup_executor_relationship: Optional[str] = Field(default=None, max_length=100)
    specific_gifts: Optional[str] = Field(default=None, max_length=2000)
    additional_wishes: Optional[str] = Field(default=None, max_length=2000)
    
    # Reasoning field helps the LLM explain its extraction process
    reasoning: Optional[str] = Field(default=None, max_length=2000)
