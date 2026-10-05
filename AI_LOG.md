# AI Log: Engineering Decisions & Collaboration

This log documents the AI-assisted development of the Document Intake Assistant. Rather than relying on AI as a simple code generator, I utilized it as a pair-programming partner to enforce rigorous software engineering patterns—specifically focusing on bounding the non-deterministic nature of LLMs into a highly predictable, type-safe pipeline.

## 1. Bounding the LLM (The "State" Anti-Pattern)
**The Problem:** The most common mistake in LLM-wrapper applications is using the raw conversation history as the source of truth. This leads to hallucinations, dropped context, and impossible state reconciliation.
**The Prompt:** *"We need to decouple the conversation from the system state. Let's design a FastAPI backend where the source of truth is a strictly typed Pydantic v2 `IntakeState` model. The LLM's only job is to return a transient `ExtractionResult` which we will immutably merge into the master state."*
**Notable Iteration:** 
The AI initially generated loose typing (e.g., `children_names: Optional[str]`). I corrected it to enforce strict list typing (`List[str] | None = None`) and implemented a deep-copy merge strategy in the `StateManager` to ensure state mutations never corrupt the active session memory.

## 2. Engineering a Deterministic Local Stub
**The Problem:** The prompt allowed for a mock LLM, but a simple hard-coded script wouldn't demonstrate real-world handling of simultaneous field extraction or ambiguous inputs.
**The Prompt:** *"Build a `MockLLMProvider` implementing our abstract `LLMProvider` interface. It shouldn't just return static JSON. It needs to parse multiple semantic intents in a single turn using regex heuristics (e.g., extracting both 'Name' and 'Relationship' from 'My brother, James')."*
**Correction & Refinement:** 
During testing, I noticed the AI's regex mock accidentally conflated the user skipping the "Backup Executor" (by saying "None") with them having "None" for specific gifts. I intervened and pair-programmed a contextual guardrail: if the `StateManager` is currently awaiting a backup executor, the mock strictly maps "None" to that specific entity and aborts cascading to the gifts extraction block.

## 3. Defensive Security (XSS & Application Layer DoS)
**The Problem:** Generative AI tools frequently overlook basic security principles when rendering Markdown or accepting arbitrary length strings.
**The Prompt:** *"Act as a security auditor. We are taking user strings, passing them through state, and rendering them as Markdown via React's `dangerouslySetInnerHTML`. Identify the vulnerabilities and patch them."*
**Implementation:**
We collaboratively integrated `DOMPurify` on the frontend to sanitize the Markdown payload before rendering, completely neutralizing XSS injection attacks. Furthermore, I enforced `max_length=2000` constraints on all Pydantic string fields to prevent memory-exhaustion DoS attacks via the extraction endpoints.

## 4. Resilience & The User Experience
**The Problem:** A legal intake tool must feel robust. Losing an entire session on a page reload is unacceptable.
**The Prompt:** *"Implement session recovery. The frontend must persist the `IntakeState` and chat history so a page refresh doesn't destroy the user's progress. Also, engineer a clean Blob-based export function to download the Draft Document as a Markdown file."*
**Result:** 
The AI successfully wired a `useEffect` hook to serialize the state to the browser's `localStorage`. This demonstrates an understanding of how stateless REST APIs must interact with stateful client environments to produce a resilient, production-feeling user experience.
