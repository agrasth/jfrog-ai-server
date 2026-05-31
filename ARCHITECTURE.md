# jf chat — Architecture & Design

> AI documentation assistant for JFrog CLI. Ask any JFrog question in natural language directly from the terminal.

---

## System Overview

```mermaid
graph TB
    subgraph "JFrog Documentation"
        R1[rdme-artifactory]
        R2[rdme-pipelines]
        R3[rdme-security]
        R4[rdme-... × 9 more]
    end

    subgraph "jfrog-ai-indexer"
        C[chunker.py<br/>markdown → chunks]
        E[embedder.py<br/>sentence-transformers]
        I[index_builder.py<br/>FAISS IndexFlatIP]
        G[generate_pairs.py<br/>Q&A training data]
    end

    subgraph "Artifactory — ecosysjfrog"
        AF1[(faiss.index<br/>4.2 MB)]
        AF2[(chunks.json<br/>30 MB)]
        AF3[(llama3-8b-q4.gguf<br/>4.6 GB)]
    end

    subgraph "jfrog-ai-server"
        S[search.py<br/>FAISS query]
        P[prompt.py<br/>prompt builder]
        L[llm.py<br/>Llama 3 8B]
        M[main.py<br/>FastAPI + SSE]
    end

    subgraph "JFrog CLI"
        CLI[jf chat<br/>Go command]
        INT[interactive.go<br/>multi-turn loop]
    end

    R1 & R2 & R3 & R4 --> C
    C --> E --> I
    I --> AF1
    I --> AF2
    AF3 --> L
    AF1 --> S
    AF2 --> S

    CLI --> M
    INT --> M
    M --> S --> P --> L --> M
```

---

## Query Flow (per request)

```mermaid
sequenceDiagram
    participant User as Developer
    participant CLI as jf chat (Go)
    participant Server as FastAPI Server
    participant FAISS as FAISS Index
    participant LLM as Llama 3 8B

    User->>CLI: jf chat "how do I publish Maven artifact?"
    CLI->>Server: POST /v1/chat {"query": "..."}
    Server->>FAISS: embed query → search top-3 chunks
    FAISS-->>Server: [{text, source, score}, ...]
    Server->>Server: build prompt (system + chunks + history + query)
    Server->>LLM: stream(prompt)
    loop SSE stream
        LLM-->>Server: token
        Server-->>CLI: data: "token"
        CLI-->>User: print token
    end
    Server-->>CLI: data: [DONE]
    Server-->>CLI: data: {"sources": [...]}
    CLI-->>User: (optional) Sources: rdme-artifactory/...
```

---

## Indexing Pipeline

```mermaid
flowchart LR
    A[Clone rdme-* repos<br/>12 GitHub repos] --> B[chunker.py<br/>~375 words/chunk<br/>37-word overlap]
    B --> C[embedder.py<br/>all-MiniLM-L6-v2<br/>384-dim vectors]
    C --> D[index_builder.py<br/>FAISS IndexFlatIP<br/>cosine similarity]
    D --> E[(faiss.index)]
    D --> F[(chunks.json)]
    E & F --> G[Artifactory<br/>ai-chat/]

    style A fill:#1a2a1a,stroke:#40a84b,color:#e6edf3
    style G fill:#1a1a2a,stroke:#60a5fa,color:#e6edf3
```

**Output:** 13,466 chunks from 12 JFrog product documentation repos.

---

## Auto-reindex Flow

```mermaid
flowchart TD
    A[Docs updated in rdme-* repo] --> B{Trigger type}
    B -->|merge to main| C[repository_dispatch event]
    B -->|daily midnight UTC| D[cron schedule]
    B -->|manual| E[workflow_dispatch]
    C & D & E --> F[GitHub Actions: reindex.yml]
    F --> G[python index.py]
    G --> H[New faiss.index + chunks.json]
    H --> I[Upload to Artifactory ai-chat/]
    I --> J[Server reloads index on next request]

    style F fill:#1a1a2a,stroke:#60a5fa,color:#e6edf3
    style I fill:#1a2a1a,stroke:#40a84b,color:#e6edf3
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Artifactory — ecosysjfrog.jfrog.io"
        A1[ai-chat/faiss.index]
        A2[ai-chat/chunks.json]
        A3[ai-chat/llama3-8b-q4.gguf]
        A4[ai-docker/jf-chat-server:latest]
    end

    subgraph "Inference Server"
        D[Docker Container<br/>jf-chat-server]
        D -->|pulls on startup| A1
        D -->|pulls on startup| A2
        D -->|pulls on startup| A3
    end

    subgraph "Endpoint"
        EP[ecosysjfrog.jfrog.io/ai/v1/chat]
    end

    D --> EP

    C1[Customer A: jf chat] --> EP
    C2[Customer B: jf chat] --> EP
    C3[Customer C: jf chat] --> EP

    style D fill:#1a1a2a,stroke:#60a5fa,color:#e6edf3
    style EP fill:#1a2a1a,stroke:#40a84b,color:#e6edf3
```

---

## RAG vs Fine-tuning

| Approach | What it does | When to use |
|---|---|---|
| **RAG (current)** | Retrieves relevant doc chunks at query time, feeds to base Llama 3 | Always — keeps answers grounded in current docs |
| **Fine-tuning (v2)** | Trains model weights on 12k JFrog Q&A pairs | Improves JFrog-specific tone and accuracy |
| **RAG + Fine-tuning** | Best of both — fine-tuned model + fresh doc retrieval | Production v2 target |

---

## Cost Model

| Solution | Cost per 1M queries | Data privacy | Offline |
|---|---|---|---|
| OpenAI GPT-4o | ~$5,000–15,000 | ❌ leaves JFrog infra | ❌ |
| Anthropic Claude | ~$3,000–9,000 | ❌ leaves JFrog infra | ❌ |
| **jf chat (Llama 3 + RAG)** | **$0** | ✅ fully local | ✅ |

---

## Component Responsibilities

### jfrog-ai-indexer

| File | Responsibility |
|---|---|
| `chunker.py` | Split markdown into overlapping text chunks |
| `embedder.py` | Generate 384-dim sentence embeddings |
| `index_builder.py` | Build + save FAISS index and chunks.json |
| `uploader.py` | Upload artifacts to Artifactory |
| `index.py` | Orchestrate the full pipeline |
| `generate_pairs.py` | Generate Q&A training pairs via local LLM |

### jfrog-ai-server

| File | Responsibility |
|---|---|
| `search.py` | Load FAISS index, embed query, return top-k chunks |
| `prompt.py` | Build LLM prompt from system message + chunks + history |
| `llm.py` | Load Llama 3 GGUF, stream tokens |
| `main.py` | FastAPI app — `/v1/chat` SSE endpoint + `/health` |
| `finetune.py` | LoRA fine-tuning via Unsloth (optional, requires GPU) |

### jfrog-cli (general/chat/)

| File | Responsibility |
|---|---|
| `cli.go` | `jf chat` command entrypoint, flag parsing |
| `client.go` | HTTP POST to server, SSE stream reader |
| `interactive.go` | Multi-turn conversation loop (`--interactive`) |
| `models.go` | `ChatRequest`, `Message` types |

---

## Key Design Decisions

**Why FAISS instead of a vector database?**
FAISS index is a single file stored as an Artifactory artifact. No separate database to run or maintain. For 13k chunks it's fast enough (<10ms retrieval) and simple to update.

**Why Llama 3 8B Q4_K_M?**
~4.7GB quantized — fits in RAM, runs on CPU without GPU. Performance is sufficient for documentation Q&A where context is provided via RAG.

**Why SSE streaming?**
Token-by-token streaming gives instant feedback even for long answers. Go's `bufio.Scanner` handles SSE parsing natively without additional libraries.

**Why sentence-transformers all-MiniLM-L6-v2?**
384-dim embeddings, ~80MB model, fast CPU inference, good retrieval quality for technical documentation. Same model used in both the indexer and the server ensures embedding space consistency.
