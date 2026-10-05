# Document Intake Assistant

A full-stack web application designed to conduct a conversational interview, maintain an explicitly structured internal state, and produce a **Fictional Personal Wishes Document**.

This repository was created as an engineering technical test to evaluate LLM application design, strict state parsing, live preview generation, and combining generative AI with conventional software engineering.

## Key Features

1. **Deterministic Smart Mock Engine**: Designed to work reliably without paid API access. The LLM Mock uses robust heuristics, entity extraction, and semantic context inference to parse single or multiple fields from conversational data. (Can be swapped with OpenAI/Claude/Gemini easily via the abstract `LLMProvider` interface).
2. **Strict Schema & Source of Truth**: The conversation history alone is NOT the source of truth. Validated `IntakeState` (using Pydantic v2) stores the confirmed facts, and missing fields trigger follow-up heuristics in the `StateManager`. Unknown or unconfirmed values are explicitly represented as `None`.
3. **Live Syncing Previews**: Instantly view the structured JSON state side-by-side with the rendering draft of the Personal Wishes Document.
4. **Correction Engine**: Users can correct previously supplied information at any point (e.g., "Actually my executor is Sarah, not James"). The state updates cleanly without mutating prior turns.
5. **Clear Legal Disclaimers**: Draft documents are prominently labeled as fictional drafts and not legal advice.

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic v2, Pytest, HTTPX
- **Frontend**: React 19, Vite, Lucide Icons, Pure CSS
- **Design System**: Responsive split-pane UI with dark-theme default.

## Getting Started

### Prerequisites
- Node.js v18+
- Python 3.10+
- `pip` and `npm`

### 1. Run the Backend

```bash
cd backend
python -m venv venv

# Activate venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy environment configuration
cp .env.example .env

# Run backend API
uvicorn app.main:app --reload --port 8000
```
Backend API will be available at `http://localhost:8000` (Health check: `http://localhost:8000/health`).

### 2. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend will be available at `http://localhost:5173`.

## Architecture Details

- `backend/app/models/schema.py`: Explicit Pydantic contract definition (`IntakeState`, `ExtractionResult`, `ChatRequest`, `ChatResponse`).
- `backend/app/services/llm_provider.py`: Abstract interface and provider factory (`get_llm_provider`) standardizing LLM interactions.
- `backend/app/services/mock_llm.py`: Smart deterministic entity extraction engine acting as a local stub.
- `backend/app/services/state_manager.py`: Responsible for managing state merges (`model_copy(deep=True)`), validating schema updates, and determining next logical questions.
- `backend/app/services/document_generator.py`: Turns the validated structural state into the final Markdown draft document with required disclaimers.

## Swapping the Mock with a Real LLM Provider

The application is built around the `LLMProvider` interface in `backend/app/services/llm_provider.py`. To plug in OpenAI / Claude / Gemini:
1. Set `LLM_PROVIDER=openai` in `backend/.env` and configure `OPENAI_API_KEY`.
2. Implement `extract_and_respond` using OpenAI's Structured Outputs (`client.beta.chat.completions.parse`) with `response_format=ExtractionResult`.
3. The rest of the state manager, document generator, and frontend remain unchanged.

## Running Tests

In the `backend` directory, run:
```bash
pytest tests/
```
The test suite validates:
- `test_state.py`: State merges, deep immutability, entity extraction heuristics, document generation, and FastAPI endpoints.
- `test_fixtures.py`: Fixture-driven validation against `tests/fixtures.json` covering valid, ambiguous, and malformed model inputs.

## Production Improvements
If this application were moved to a production environment, I would make the following improvements:
1. **Real LLM Integration**: Replace the `MockLLMProvider` with the real OpenAI/Claude integration using Structured Outputs. The current architecture allows this natively via the `LLMProvider` interface.
2. **Database Persistence**: Currently, session states are ephemeral in the backend (relying on the client sending the state) and persisted in the frontend via `localStorage`. For production, I would add a PostgreSQL database with SQLAlchemy to track session progress and implement user authentication.
3. **Enhanced Validation & Retry Logic**: Add logic to handle cases where a real LLM hallucinates an invalid response or a 422 error is returned. The LLM would be prompted in a loop to self-correct its JSON output if it fails Pydantic validation.
4. **Export Service**: Convert the Markdown draft document into a stylized PDF using a backend rendering library (like WeasyPrint or ReportLab) instead of relying purely on frontend blob generation.
5. **Rate Limiting & Security**: Add robust rate-limiting to the FastAPI backend to prevent API abuse, and strict CORS rules for the frontend.
