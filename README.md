# Document Intake Assistant: A Deterministic Approach to LLM State

A full-stack web application engineered to conduct a conversational interview, strictly maintain a structured internal state machine, and dynamically render a **Fictional Personal Wishes Document**. 

This repository was designed specifically to demonstrate how to tame the non-deterministic nature of LLMs by wrapping them in rigorous software engineering patterns, typed contracts, and immutable state management.

## 🏗️ Architectural Philosophy

The core design principle of this application is **State Machine over Conversation History**. 

In naive LLM applications, the conversation history is treated as the source of truth, leading to context-window exhaustion, hallucinations, and unresolvable state conflicts. 
In this architecture:
1. **The LLM is merely a transient parser.** It takes a single user string and returns an ephemeral `ExtractionResult`.
2. **The `IntakeState` (Pydantic v2) is the absolute source of truth.**
3. **The `StateManager` acts as the reducer.** It immutably merges the LLM's extraction into the master state and algorithmically determines the next question based on missing fields.

### Key Capabilities
- **Simultaneous Field Extraction:** The engine correctly handles complex semantic inputs (e.g., extracting both Name and Relationship from "My brother, James" in a single turn).
- **Graceful Correction Routing:** Users can override previously established facts at any point (e.g., "Actually change my executor to Alice"). The state updates cleanly without confusing the conversation flow.
- **Resilient Memory:** The React frontend caches the serialized state and conversation log to `localStorage`, ensuring the session survives accidental browser refreshes.
- **Zero-Trust Security:** Markdown rendering via React's `dangerouslySetInnerHTML` is protected against XSS injection via `DOMPurify`. The backend Pydantic models enforce strict string limits to mitigate memory-exhaustion DoS attacks.

## 💻 Tech Stack

- **Backend:** Python 3.10+, FastAPI, Pydantic v2, Pytest
- **Frontend:** React 19, Vite, Lucide Icons, DOMPurify
- **LLM Engine:** Abstract `LLMProvider` interface (currently backed by a highly capable regex/heuristic `MockLLMProvider` stub for local, key-less execution).

## 🚀 Getting Started

### Prerequisites
- Node.js v18+
- Python 3.10+

### 1. Bootstrapping the API (Backend)
```bash
cd backend
python -m venv venv

# Activate venv (Windows)
.\venv\Scripts\Activate.ps1
# Activate venv (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Uvicorn server
uvicorn app.main:app --reload --port 8000
```
*The API mounts at `http://localhost:8000`. Run the test suite via `pytest tests/`.*

### 2. Starting the Client (Frontend)
```bash
cd frontend
npm install
npm run dev
```
*The UI mounts at `http://localhost:5173`.*

## 🔌 Swapping the Mock for a Production LLM

The application was built adhering to the Dependency Inversion principle. The `MockLLMProvider` can be cleanly swapped for OpenAI, Anthropic, or Gemini without touching the State Manager or Document Generator.

1. Create `backend/.env` and set `LLM_PROVIDER=openai` (with `OPENAI_API_KEY=...`).
2. Implement the `extract_and_respond` method in a new `OpenAIProvider` class utilizing OpenAI's **Structured Outputs API** (`client.beta.chat.completions.parse`).
3. Pass `ExtractionResult` as the `response_format`. The LLM is now forced to adhere to our strict Pydantic contract.

## 📈 Roadmap for Production Readiness

While this architecture solves the core problems of state ambiguity, deploying to production would require the following infrastructure upgrades:

1. **Persistent Datastores:** Replace `localStorage` with a PostgreSQL database and SQLAlchemy ORM to track distributed user sessions and support OAuth2 authentication.
2. **Self-Healing LLM Pipelines:** If utilizing a real LLM, introduce a retry loop within the Provider layer to handle `ValidationError` exceptions. If the LLM hallucinates malformed JSON, the exception stack trace should be fed back to the LLM to self-correct.
3. **Server-Side PDF Rendering:** Migrate the client-side Blob generation for Document Export to a robust backend rendering engine like ReportLab or WeasyPrint for professional, styling-consistent PDFs.
4. **API Gateway & Rate Limiting:** Introduce Redis-backed rate limiting on the `/api/chat` endpoint to protect expensive LLM tokens from abuse.
