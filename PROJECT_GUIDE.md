# AI Code Assistant Project Guide

This document explains the full flow of the project, how each part works, and where each responsibility lives.

---

## 1. What this project does

This project is a small AI-powered coding assistant with three main capabilities:

- Explain existing code
- Generate new code using Retrieval-Augmented Generation (RAG)
- Execute generated Python safely

It is built with:

- FastAPI for the backend API
- Streamlit for the frontend UI
- LangChain for prompt and retrieval orchestration
- ChromaDB for vector search
- Hugging Face embeddings for semantic search
- OpenRouter for LLM access

---

## 2. High-level architecture

The flow is:

1. User sends a message from the frontend or API
2. The backend classifies the request as either:
   - Explain
   - Generate
3. If the request is Explain, the system sends the code to the LLM for explanation
4. If the request is Generate, the system:
   - searches the vector database
   - checks whether the retrieved context is relevant
   - generates code using that context
   - optionally executes the generated code
5. The answer is returned to the UI and the conversation memory is updated

---

## 3. Main project structure

Here is the role of each folder and file.

### Root files

- app.py
  - Entry point for the application
  - Starts the FastAPI app through uvicorn

- main.py
  - Defines the FastAPI application
  - Includes the chat router

- config.py
  - Loads environment settings
  - Holds API keys, model names, database path, and logging path

- requirements.txt
  - Lists all dependencies needed to run the project

- .env.example
  - Example environment file with required variables

- README.md
  - Quick start and overview

### Routers

- routers/chat.py
  - Exposes the API endpoints
  - Handles /chat, /learn, /rebuild, and /health

### Services

This is where the business logic lives.

- services/classifier.py
  - Decides whether the request is an Explain or Generate request
  - Uses an LLM when available, otherwise falls back to simple keyword logic

- services/retriever.py
  - Ingests the Hugging Face dataset
  - Builds ChromaDB from the dataset
  - Stores documents as embeddings on disk
  - Supports adding user-learned solutions later

- services/relevance.py
  - Checks whether the retrieved context is relevant enough to answer the question

- services/generator.py
  - Sends prompts to the LLM and returns generated code or explanation

- services/code_runner.py
  - Executes generated Python code safely in a subprocess

- services/memory.py
  - Stores recent chat history so the assistant can remember prior messages

- services/rag.py
  - Coordinates the whole assistant flow
  - Calls classifier, retriever, relevance checker, generator, runner, and memory

### Models

- models/schemas.py
  - Defines request and response Pydantic models
  - Ensures clean input and output validation

### Frontend

- frontend/streamlit_app.py
  - Simple chat UI built with Streamlit
  - Sends messages to the backend and displays the response

### Ingestion

- ingestion/ingest.py
  - Script that rebuilds the vector database from the Hugging Face dataset

### Tests

- tests/test_smoke.py
  - Basic smoke tests for classifier and code execution

---

## 4. How the request flow works

### A. User sends a message

The user may type something like:

- “Explain this code”
- “Write a Python function to reverse a string”
- “Generate code for a binary search”

This message enters the backend through the /chat endpoint.

### B. Intent classification

The message first passes through the classifier.

The classifier looks at the user request and decides whether it is:

- Explain
- Generate

If the request says “explain,” the system uses the explanation path.
If it says “generate” or looks like a coding request, it uses the RAG path.

### C. Explain path

If the intent is Explain, the assistant:

- does not use the vector database
- sends the user’s code to the LLM
- asks the LLM to explain the code line by line
- returns a structured explanation with:
  - purpose
  - logic
  - complexity
  - possible improvements

### D. Generate path

If the intent is Generate, the assistant does the following:

1. Takes the user’s question
2. Converts it to a vector embedding
3. Searches ChromaDB for the top 5 most similar documents
4. Builds a retrieval context from those documents
5. Checks if the retrieved context is relevant
6. If relevant, generates code from the retrieved context
7. Optionally executes the code

This is the RAG flow.

---

## 5. How RAG works here

RAG stands for Retrieval-Augmented Generation.

The system does not rely only on the LLM’s general knowledge. Instead, it first retrieves relevant example documents from a local knowledge base.

### Why this helps

The LLM can answer more accurately when it has domain-specific examples from the dataset.

### The RAG process

1. The user asks a question
2. The system embeds that question
3. The system searches the vector database
4. The system gets the top 5 closest documents
5. The system uses those documents as context for generation

---

## 6. How the knowledge base is built

The vector database is created from the Hugging Face dataset openai/openai_humaneval.

### Dataset ingestion flow

1. The ingestion script runs
2. The retriever loads the test split of the Hugging Face dataset
3. Each item is converted into a document
4. Each document includes:
   - task ID
   - prompt
   - canonical solution if available
   - test cases
   - metadata like entry point and source
5. The documents are split into chunks
6. Those chunks are embedded and stored in ChromaDB

### Why chunking is needed

Large documents are split into smaller pieces so retrieval is more precise and efficient.

The project uses:

- chunk size: 300
- chunk overlap: 50

---

## 7. Where the embeddings and vector DB live

The vector database is stored in:

- database/chroma_db/

This directory persists across restarts, so the knowledge base survives application restarts.

---

## 8. How code execution works

After generated code is produced, the assistant can run it safely.

### Safety approach

The code runner uses Python’s subprocess module to run code in a temporary file.

The system:

- writes generated Python to a temp file
- runs it using Python
- captures stdout and stderr
- returns whether execution succeeded or failed

This is intentionally limited to Python code only and avoids unsafe shell execution.

---

## 9. How memory works

The assistant stores prior conversation messages.

This is handled by the memory module.

### What memory does

- saves the user’s previous messages
- saves assistant replies
- uses them as context for later prompts

This helps the assistant feel more conversational.

---

## 10. How the API is structured

The FastAPI backend exposes these endpoints:

### /health

Returns OK

Used to verify the service is alive.

### /chat

Accepts a message and returns:

- intent
- answer
- retrieved documents
- execution result

### /learn

Accepts a question and a solution from the user.

This stores the solution in the vector database for future retrieval.

### /rebuild

Deletes and rebuilds the vector database.

This is useful when you want to refresh the knowledge base.

---

## 11. How the frontend works

The Streamlit UI provides a simple chat experience.

It does the following:

- shows the conversation history
- accepts a new user prompt
- sends the prompt to /chat
- displays the assistant response
- shows detected intent and execution output

---

## 12. What each Python file is responsible for

### config.py

This is the central configuration loader.

It reads environment variables such as:

- OPENROUTER_API_KEY
- OPENROUTER_BASE_URL
- MODEL_NAME
- EMBEDDING_MODEL

### models/schemas.py

This defines structured Pydantic models for the backend.

It ensures the API input and output are clean and predictable.

### services/classifier.py

This decides which path to take.

If the request is about explaining code, it chooses Explain.
Otherwise it chooses Generate.

### services/retriever.py

This is the heart of the retrieval system.

It:

- loads the dataset
- turns data into documents
- splits documents into chunks
- embeds them
- stores them in ChromaDB

### services/relevance.py

This checks whether the retrieved examples are actually useful.

If they don’t match the question closely enough, the system stops and asks the user to provide a better solution.

### services/generator.py

This sends the prompt to the LLM.

It can generate either:

- explanatory text
- code

### services/code_runner.py

This handles execution of generated Python.

It is completely separate from generation, which keeps the design modular.

### services/rag.py

This is the orchestrator.

It wires everything together into one assistant pipeline.

---

## 13. Why the design is modular

The project follows a clean separation of responsibility:

- routers handle API concerns
- services handle business logic
- models validate data
- frontend handles UI
- ingestion handles knowledge base construction

This makes the project easier to extend and maintain.

---

## 14. How to run the project

### Install dependencies

```bash
pip install -r requirements.txt
```

### Build the vector database

```bash
python ingestion/ingest.py
```

### Start backend

```bash
uvicorn app:app --reload
```

### Start frontend

```bash
streamlit run frontend/streamlit_app.py
```

### Or use the launcher

On Windows:

```bat
run_all.bat
```

or

```bat
start_both.bat
```

---

## 15. How to test it

### Test the backend health endpoint

Open:

- http://127.0.0.1:8002/health

### Test the API docs

Open:

- http://127.0.0.1:8002/docs

### Test the chat endpoint

Send a request with a message like:

```json
{
  "message": "Explain this code: def add(a,b): return a+b"
}
```

### Test the UI

Open:

- http://127.0.0.1:8501

### Run tests

```bash
pytest -q
```

---

## 16. What you should understand if you wrote it yourself

If you understand the project well, you should be able to explain this:

- The frontend sends a message to the API
- The API routes the request into the service layer
- The classifier decides the intent
- The explain path returns explanation without retrieval
- The generate path uses retrieval before generation
- The retriever uses ChromaDB and embeddings to search prior knowledge
- The generator uses the retrieved context and the LLM to produce code
- The runner executes code safely
- The memory layer keeps the conversation coherent

That is the core mental model of the project.

---

## 17. Summary

This project is a layered AI assistant built around four ideas:

1. Intent classification
2. Retrieval-Augmented Generation
3. Safe code execution
4. Conversation memory

The structure is modular on purpose so each piece can be changed independently.

If you understand these layers, you understand the project.
