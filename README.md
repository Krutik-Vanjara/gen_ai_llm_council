

# 🏛️ Distributed LLM Council

> **A Distributed Multi-model Local AI System powered by Ollama and Tailscale.**

## 📖 Project Overview

This project is an advanced refactor of Andrej Karpathy's **LLM Council**. We have removed all cloud-based dependencies (OpenRouter/OpenAI) and replaced them with a **distributed local architecture**. Multiple machines across different operating systems (Windows, Kali Linux, and WSL2) collaborate to answer, review, and synthesize responses to user queries.

## 📡 Distributed Infrastructure

The system is distributed across four physical machines connected via a **Tailscale Mesh VPN**, allowing secure communication between diverse OS environments.
![Distributed AI Layout](https://github.com/Krutik-Vanjara/gen_ai_llm_council/blob/main/web1.excalidraw%20(3).png)
| Role | Name | IP Address | OS | Model |
| --- | --- | --- | --- | --- |
| **👑 Chairman** | `abhi` | `100.114.119.33` | Windows | `llama3.2:3b` |
| **⚖️ Council 1** | `JD` | `100.64.243.5` | Windows | `gemma2:2b` |
| **⚖️ Council 2** | `Krutik` | `100.123.209.93` | Linux (WSL2) | `llama3.2:1b` |
| **⚖️ Council 3** | `Samuel` | `100.120.97.23` | Windows | `qwen2.5:3b` |

## ⚙️ Council Workflow

The system implements a mandatory 3-stage deliberation process:

1. **Stage 1: First Opinions** - Council members receive the query and generate independent responses in parallel using `asyncio`.
2. **Stage 2: Review & Ranking** - Each member reviews and ranks the other responses anonymously to ensure unbiased peer critique.
3. **Stage 3: Synthesis** - The **Chairman LLM** (running on a dedicated node) receives all outputs and rankings to generate a final authoritative response.

## 🛠️ Technical Key Features

* **Asynchronous Orchestration:** Developed with **FastAPI** to handle parallel REST API calls to distributed Ollama instances.
* **Persistent Context:** A custom `memory_manager.py` maintains session history via `council_memory.json` to allow multi-turn conversations.
* **Live Node Monitoring:** The Streamlit frontend includes a real-time health check for each distributed node's Ollama service.

## 📂 Directory Structure

```text
llm-council-local/
├── Readme.md               # Project documentation
├── requirements.txt        # Python dependencies
├── backend/
│   ├── main.py             # FastAPI entry point (Chairman)
│   ├── config.py           # Tailscale IP & Model mappings
│   ├── council.py          # 3-Stage orchestration logic
│   └── memory_manager.py   # Local JSON persistence
└── frontend/
    └── dashboard.py        # Streamlit UI with Node Monitor

```

## 🚀 Setup & Installation

### 1. Node Preparation

On every machine, ensure **Ollama** is installed and serving on the network interface:

* **Windows:** `$env:OLLAMA_HOST="0.0.0.0:11434"; ollama serve`
* **Linux:** `OLLAMA_HOST=0.0.0.0:11435 ollama serve`

### 2. Environment Setup

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt

```

### 3. Execution

Run the Chairman backend and the user interface from the `samuel-pc` or `abhi` node:

```bash
# Start Backend
python -m uvicorn backend.main:app --host 100.114.119.33 --port 8000

# Start Frontend
streamlit run frontend/dashboard.py

```

---

**Team Members:** Abhi, JD, Krutik, Samuel | **TD Group:** [Your Group Name]

