# AI Log: Development Process & Decisions

*This log documents my use of AI (acting as an advanced autocomplete and sounding board) while building the Document Intake Assistant. In line with the submission instructions, this log is candid about where the AI failed and how I applied engineering judgement to correct it.*

### 1. Defining the Domain Model (The "State" vs "Context" Problem)
**Goal:** Prevent the classic LLM trap of relying on raw conversation history as the source of truth.
**My Prompt:** *"Create a FastAPI backend for a Document Intake Assistant. Use Pydantic v2 to define a rigid `IntakeState` and `ExtractionResult` schema capturing the required fields (name, address, worldwide assets, children, executor, gifts, wishes). The LLM should only return `ExtractionResult`."*
**AI Output I Questioned:** The AI generated loose typings like `children_names: Optional[str] = None` and allowed arbitrary kwargs in the schema.
**My Correction:** I immediately rejected this. If we allow unstructured strings for list objects, the downstream document generation will eventually break. I forced the AI to strictly type it as `List[str] | None = None` and configured Pydantic to reject extra attributes, ensuring the LLM couldn't hallucinate unhandled keys.

### 2. Handling State Merges and Immutability
**Goal:** Ensure that when a user corrects previous information (e.g. "Actually my executor is Sarah"), the state updates deterministically without mutating active memory references.
**My Prompt:** *"Create a `StateManager` class with a `merge_state` method. It must take the current `IntakeState` and an `ExtractionResult` and return a deeply copied new state."*
**AI Output I Questioned:** The AI wrote a shallow copy merge: `new_state = current_state.copy()`. 
**My Correction:** I corrected the AI to use Pydantic's `model_copy(deep=True)` because the `executor` field is a nested object. A shallow copy would have caused nested mutations to bleed across chat turns, breaking the predictability and time-travel debugging capabilities of the session. 

### 3. Implementing the Deterministic Mock LLM Guardrails
**Goal:** Create a robust local stub that handles ambiguous and contradictory human input.
**My Prompt:** *"Build a `MockLLMProvider` using regex to simulate entity extraction. It needs to handle edge cases, like a user answering multiple questions at once."*
**AI Output I Questioned:** The AI wrote a decent regex block, but it had a severe logic overlap. If the user was asked for a Backup Executor and replied "None", the AI's naive regex aggressively matched "None" and assigned it to `specific_gifts = "None"` instead, bypassing the executor logic entirely.
**My Correction:** This perfectly demonstrated why we can't blindly trust generative or regex parsing without context. I manually rewrote the `mock_llm.py` conditional blocks to inject contextual awareness: if the `StateManager` is currently awaiting a backup executor, a "None" response is strictly mapped to the executor state, halting the `specific_gifts` extraction block for that specific turn.

### 4. Security Auditing (XSS & DoS)
**Goal:** Ensure the application is secure by design, despite being a prototype.
**My Prompt:** *"Review the React frontend and FastAPI backend for XSS and DoS vulnerabilities. The Fictional Document live preview currently uses React's `dangerouslySetInnerHTML`."*
**AI Output I Questioned:** The AI suggested writing a custom regex sanitization function for the frontend Markdown parser to strip out `<script>` tags.
**My Correction:** I rejected the custom regex (as rolling custom security sanitization is a well-known anti-pattern) and instructed the AI to import and implement `DOMPurify` instead. On the backend, I instructed the AI to add `max_length=2000` constraints on all Pydantic string fields, mitigating potential Memory Exhaustion (DoS) attacks on the extraction endpoints.

### Summary of Judgement
Throughout development, the AI was excellent at scaffolding boilerplate (React components, FastAPI routing), but it consistently failed at edge-case state management and strict data validation. By treating the AI as a junior developer and enforcing strict architectural boundaries (Pydantic, Immutability, DOMPurify), I ensured the final application was deterministic and reliable.
