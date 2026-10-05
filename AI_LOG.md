# AI Log

This document serves as a brief log of the AI collaboration used to build the Document Intake Assistant, satisfying the submission requirement to include "a brief AI log with key prompts, notable iterations, and examples of output questioned or corrected."

## 1. Initial Scaffold and Architecture
**Prompt Strategy:**
We started by defining the strict Pydantic schemas required to hold the structured state.
*Prompt:* "Create a FastAPI backend for a Document Intake Assistant. Use Pydantic v2 to define an `IntakeState` and `ExtractionResult` schema capturing full name, address, worldwide assets, children, executor, specific gifts, and additional wishes. Then create an abstract `LLMProvider` interface."

**Notable Iterations:**
- *Correction:* The initial AI generated schema had `children_names` as an optional string. I corrected it to `List[str] | None = None` to enforce structured data collection.
- *Decision:* We opted to maintain the source of truth purely in the `IntakeState` object instead of extracting from a massive chat history block every turn. The `ExtractionResult` explicitly handles incremental updates.

## 2. Implementing the Mock LLM
**Prompt Strategy:**
Since the assignment allowed for a local stub/mock when an LLM API was unavailable, we built a smart deterministic regex-based mock.
*Prompt:* "Implement a `MockLLMProvider` that satisfies the `LLMProvider` interface. It should use regex and heuristics to extract information from user messages and return an `ExtractionResult`. Ensure it can handle users answering multiple fields at once (e.g., 'I have 2 kids: Alice and Bob')."

**Output Questioned & Corrected:**
- *Issue:* The AI originally implemented a mock that would accidentally capture "None" as a specific gift when the user was actually skipping the Backup Executor prompt.
- *Correction:* I caught this state overlap. I instructed the AI to update the `mock_llm.py` logic so that if the conversation state was currently awaiting a "Backup Executor", a response of "None" would safely map to `backup_executor_name = "None"` and explicitly bypass the `specific_gifts` extraction block for that turn.

## 3. Conversational State Manager
**Prompt Strategy:**
We needed a State Manager to figure out what to ask next based on the null fields in the Pydantic model.
*Prompt:* "Create a `StateManager` class. It needs a `merge_state` method that takes the current `IntakeState` and an `ExtractionResult` and merges them without mutating the original. It also needs a `get_next_question` method that linearly checks the state for `None` values and returns the next logical question."

**Notable Iterations:**
- *Ambiguity Handling:* The AI was instructed to ensure the follow-up logic correctly bypassed the "children's names" question if the `has_children` boolean was set to `False`. 

## 4. Security Hardening
**Prompt Strategy:**
I intentionally challenged the application's security to ensure it handled malformed responses gracefully.
*Prompt:* "Review the React frontend and FastAPI backend for XSS and DoS vulnerabilities. The Fictional Document live preview uses `dangerouslySetInnerHTML`. Fix it."

**Correction:**
- The AI correctly identified that user inputs (like a malicious `<img src=x onerror=alert(1)>` passed as a name) would execute in the Draft Document preview. It successfully integrated `DOMPurify` to sanitize the Markdown rendering.
- For DoS, the AI updated the Pydantic schemas to include `max_length=2000` on string fields to prevent memory exhaustion attacks.

## 5. Adding Polish: LocalStorage & Exports
**Prompt Strategy:**
*Prompt:* "Update the React frontend to persist the session in `localStorage` so the user doesn't lose progress on refresh. Also add a Download button to export the Draft Document as a Markdown file."

**Result:**
The AI seamlessly integrated a `useEffect` hook to serialize the chat and `intakeState` to localStorage, recovering it cleanly on initialization, satisfying the requirement to handle realistic application environments.
