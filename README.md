# Cognifiles - Local RAG Academic Tutor

Cognifiles is a 100% local, private, and offline Retrieval-Augmented Generation (RAG) ecosystem engineered to function as an autonomous academic tutor. This production-ready architecture allows students to upload educational PDFs, instantly parse and index knowledge bases into a local vector store, and conduct fluent chat sessions with an offline Large Language Model (LLM)—all running locally with absolute data privacy and zero external API dependencies.

---

## Architecture & Component Topology

The system is designed around a clean, decoupled, and containerized topology utilizing Vanilla RAG workflows. By avoiding heavy framework abstraction layers (e.g., LangChain or LlamaIndex), the codebase remains lightweight, predictable, and fully inspectable.

* Frontend User Interface (Streamlit): A reactive, stateful dashboard providing real-time document upload counters, sanitized collection tracking, and dynamic chat history tracking.
* Asynchronous Core API (FastAPI): Orchestrates structural text extraction via local PDF parsers, handles document workflows, manages vector context retrieval, and dispatches parallel streaming requests to the LLM backend.
* Vector Database (ChromaDB): Stores, indexes, and queries dense multi-dimensional embeddings produced strictly on-device using local all-MiniLM-L6-v2 transformer pipelines.
* NoSQL Storage (MongoDB): A secured document database dedicated to immutable storage of structured metadata, file profiles, and ingestion counts.
* Local Inference Host (Ollama): A native inference runner executing the highly optimized Llama 3.2 (1B) model directly on local hardware.

---

## System Dependencies & Build Spec

The ecosystem uses uv by Astral for lightning-fast, reproducible builds driven directly by cryptographic lockfiles (uv.lock), completely bypassing traditional legacy pip environments.

Dependencies list:
- fastapi>=0.110.0          # Asynchronous high-performance web routing layer
- uvicorn[standard]         # High-concurrency ASGI production server
- pydantic>=2.7.0           # Strict runtime data modeling and environment schema enforcement
- motor>=3.3.2              # Asynchronous non-blocking MongoDB client driver
- pypdf>=4.2.0              # Pure Python local binary PDF text parsing engine
- chromadb>=0.5.0           # Enterprise-grade local vector store with embedded transformers
- httpx                     # Async HTTP client managing connections to the local Ollama instance
- streamlit>=1.59.0         # Reactive visual layer and component state manager
- requests                  # Deterministic synchronous HTTP connector for Streamlit service
- pillow>=12.2.0            # Local image and page rendering geometry helper

---

## Environment Configuration

Environment boundaries are managed seamlessly via a .env file placed in the root directory. Inside the container network, named service resolution replaces traditional loopbacks:

# API Details
API_V1_STR=/api/v1
PROJECT_NAME="Cognifiles Local Tutor"

# Internal Core Services Data Layout
CHROMA_PERSIST_DIR=/app/.chromadb_storage
MONGO_URI=mongodb://admin:secret_password@mongodb:27017/?authSource=admin

# Inference Specification
LOCAL_LLM_URL=http://ollama:11434
LOCAL_MODEL_NAME=llama3.2:1b

---

## Deployment & Operational Orchestration

The entire infrastructure lifecycle is managed elegantly through short-hand instructions inside an automated Makefile.

### 1. Step-by-Step Initialization

Launch the entire containerized architecture in detached mode:
$ make up

This instantly pulls base layers, invokes uv sync to build deterministic environments inside the containers, and hooks up isolated bridge networking.

### 2. Download the Language Model Weights
Since the isolated Ollama engine container starts clean, download and allocate the specific model weights into the persistent volume:
$ make ollama-model

### 3. Verification & Interfaces
Once operational, the system manifests on the following local interfaces:
* Student Web Interface: http://localhost:8501
* Interactive Swagger API Docs: http://localhost:8000/docs
* MongoDB Instance: Attached securely on localhost:27017

---

## Complete Makefile Command Registry

- make up: Boots all containers in the background and prints connection entrypoints.
- make down: Gracefully terminates active service containers and tears down network bridges.
- make build: Forces an immediate zero-cache rebuild of the uv-based Docker layers.
- make logs: Attaches a terminal tail to the unified multi-container stdout logs.
- make ollama-model: Directly executes model pulling protocols within the virtualized Ollama node.
- make clean: Purges localized Python artifacts (__pycache__, .pyc files) from storage.

---

## Under the Hood: The Ingestion Pipeline

1. Sanitization: The application dynamically handles collection names input by the user, stripping accents via unicodedata and substituting illegal characters or whitespace with safe delimiters (_) to meet strict ChromaDB storage requirements.
2. Structural Chunking: PDFs are ingested as chunk streams. If the resulting text block matches dense parameters, it gets segmented into distinct context blocks.
3. Cross-Reference Generation: The metadata payload is initially created in MongoDB, yielding an immutable ObjectId. This ID is passed over as the document_id reference into ChromaDB, creating a perfect data link across databases.
4. Prompt Orchestration: When a query hits /chat/query, the system retrieves the top 4 matching segments from ChromaDB, constructs a pristine context prompt, appends historical messages, and pushes a lightweight HTTP request to Ollama.