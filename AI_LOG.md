# AI Log & Engineering Notes

## 1. Key Prompts & Iterations

### Iteration 1: Explicit Structured Schema vs. Conversational History
- **Prompt Context**: *"Define an explicit schema for the information collected. Conversation history alone is not sufficient as the application's source of truth."*
- **Engineering Decision**: Modeled the intake state using Pydantic v2 (`IntakeState`). Unconfirmed properties default explicitly to `None` rather than empty strings or booleans, enabling the application to differentiate between "unconfirmed" (needs follow-up) and "explicit false" (e.g. `has_children: False`).

### Iteration 2: Handling Single-Turn Multi-Entity Extraction & Overrides
- **Prompt Context**: *"Handle answers that provide several fields at once, in any reasonable order. Allow the user to correct previously supplied information."*
- **Questioned/Corrected Output**:
  - *Initial Issue*: When parsing `"My brother James is my executor"`, naive greedy regex matched `"James is my executor"` into `executor_name` and left `executor_relationship` unparsed.
  - *Correction*: Refined the matcher with non-greedy bounded tokens (`re.search(r'my\s+(brother|sister|friend...)\s+([a-zA-Z\s]+?)(?:\s+is\s+my\s+executor|$)')`) and added support for parenthetical inputs like `"Sarah (Sister)"`.
  - *State Immutability Fix*: Identified that `model_copy()` in Pydantic v2 performs shallow copies by default. Upgraded `merge_state` to `model_copy(deep=True)` so that modifying nested `executor` attributes does not mutate past historical state references.

### Iteration 3: Graceful Malformed Model Handling & Test Fixtures
- **Prompt Context**: *"Graceful handling of model errors, malformed responses and missing configuration. Fixtures covering valid, ambiguous and malformed model responses."*
- **Action**: Created [`tests/fixtures.json`](backend/tests/fixtures.json) and [`tests/test_fixtures.py`](backend/tests/test_fixtures.py) validating:
  - Valid extraction fixtures (full name, address, scope, children, executor).
  - Ambiguous fixtures (unclear answers leaving fields unconfirmed).
  - Malformed model responses (type errors, corrupted payloads, empty strings) with validation guards in FastAPI endpoint handlers.

---

## 2. Replacing the Mock with a Production LLM Provider

The application decouples LLM extraction from conversational orchestration via the `LLMProvider` interface in [`llm_provider.py`](backend/app/services/llm_provider.py). To swap the deterministic mock with OpenAI, Claude, or Gemini:

```python
from openai import OpenAI
from app.models.schema import IntakeState, ExtractionResult
from app.services.llm_provider import LLMProvider

class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def extract_and_respond(self, user_message: str, current_state: IntakeState):
        system_prompt = (
            "You are an intake extraction engine for a Personal Wishes Document. "
            "Extract any stated facts (name, address, worldwide assets flag, children, executor, gifts, wishes) "
            "from the user's message, considering the current confirmed state. "
            "Only set fields that the user explicitly stated or corrected."
        )
        
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": f"Current State: {current_state.model_dump_json()}"},
                {"role": "user", "content": user_message}
            ],
            response_format=ExtractionResult,
        )
        
        extraction = response.choices[0].message.parsed
        return extraction, extraction.reasoning or ""
```

---

## 3. Production Readiness Roadmap

1. **Persistent Session Storage**:
   - Store session state and conversational trajectories in PostgreSQL / Redis with an `interview_session_id` cookie/header instead of transient memory.
2. **Server-Sent Events (SSE) Streaming**:
   - Stream conversational reasoning and token generation from LLM providers in real-time.
3. **Audit Trail & Version History**:
   - Record immutable timestamped state deltas for each user edit, ensuring full compliance auditing.
4. **Export Capabilities**:
   - Provide direct PDF/DOCX downloads with digital signing placeholders alongside the markdown preview.
