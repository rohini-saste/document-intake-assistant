from fastapi import APIRouter, HTTPException
from app.models.schema import ChatRequest, ChatResponse, IntakeState, ExtractionResult
from app.services.llm_provider import get_llm_provider
from app.services.state_manager import StateManager
from app.services.document_generator import DocumentGenerator

router = APIRouter()
llm_provider = get_llm_provider()
state_manager = StateManager()
doc_generator = DocumentGenerator()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # 1. Extract info from user message using LLM
        extraction, reasoning = llm_provider.extract_and_respond(request.message, request.state)
        
        # 2. Validate model output as ExtractionResult before applying to state
        if not isinstance(extraction, ExtractionResult):
            extraction = ExtractionResult.model_validate(extraction)
        
        # 3. Merge extracted info into current state
        new_state = state_manager.merge_state(request.state, extraction)
        
        # 4. Determine next question to ask
        next_question = state_manager.get_next_question(new_state)
        
        # 5. Generate draft document
        draft_doc = doc_generator.generate(new_state)
        
        return ChatResponse(
            reply=next_question,
            state=new_state,
            draft_document=draft_doc
        )
    except Exception as e:
        # Graceful handling of model or processing errors
        draft_doc = doc_generator.generate(request.state)
        return ChatResponse(
            reply="I had a little trouble understanding that. Could you please rephrase or provide the detail again?",
            state=request.state,
            draft_document=draft_doc
        )

@router.post("/reset", response_model=ChatResponse)
async def reset():
    empty_state = IntakeState()
    reply = "Hello. Let's create your Personal Wishes Document. Could you please provide your full name?"
    draft_doc = doc_generator.generate(empty_state)
    return ChatResponse(
        reply=reply,
        state=empty_state,
        draft_document=draft_doc
    )

