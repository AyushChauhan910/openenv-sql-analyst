<div align="center">

# 📊 OpenEnv SQL Analyst

### An OpenEnv-Compliant Benchmark Environment for Evaluating AI SQL Agents

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![HuggingFace](https://img.shields.io/badge/🤗%20HF%20Spaces-Live-FFD21E?style=for-the-badge)](https://huggingface.co/spaces/ayush0910/openenv-sql-analyst)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-4CAF50?style=for-the-badge)](https://openenv.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

*Can your AI agent write SQL that actually answers business questions? Find out.*

</div>

---

## 🌐 Overview

**SQL Analyst** is an [OpenEnv](https://openenv.dev)-compliant benchmark environment that evaluates the SQL generation capabilities of AI language models against a **synthetic e-commerce database**.

Agents are given a natural language business question and the full database schema, and must produce correct SQL `SELECT` queries — iteratively, within a step budget. Tasks range from simple single-table aggregations to complex window functions and CTEs, mimicking real-world data analyst challenges.

> 💡 **Why this matters:** SQL querying is a real-world bottleneck. Poorly optimized queries — missing indexes, inefficient joins, full table scans — degrade production systems under load. This environment rewards not just correctness, but the ability to reason about schema structure and query efficiency under realistic constraints.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **Agentic Loop** | Multi-step environment: agents receive feedback and can refine their SQL across steps |
| 📈 **3 Difficulty Tiers** | Easy → Medium → Hard, covering the full spectrum of real SQL work |
| 🏪 **Synthetic E-Commerce DB** | Realistic schema with orders, products, customers, and transactions |
| 🔌 **OpenAI-Compatible** | Works with any OpenAI-compatible model via HuggingFace Inference Router |
| 🐳 **Docker Deployment** | One-command launch on any machine or cloud environment |
| 📋 **Structured Logging** | `[START]`, `[STEP]`, `[END]` log format for easy benchmarking pipelines |
| ⚙️ **Model-Agnostic** | Swap any LLM via `MODEL_NAME` env variable — GPT, Qwen, Llama, and more |

---

## 🎮 Environment Design

### Action Space

Agents output a single **SQL `SELECT` statement** targeting the provided schema.

```
Type: Text
Format: Valid SQL SELECT query (SQLite-compatible)
```

### Observation Space

At each step, the agent receives:

```json
{
  "schema_info": "Full database schema description",
  "question": "What are the top 5 products by revenue last quarter?",
  "last_query_result": "...(result of previous SQL attempt, or null)...",
  "step": 3,
  "done": false
}
```

### Reward

- **1.0** — Query returns the correct answer
- **0.0** — Incorrect result or SQL error
- Agents maximize score by getting it right in as few steps as possible

---

## 📋 Task Breakdown

| Task | Difficulty | SQL Concepts Tested | Max Steps |
|---|---|---|---|
| `easy_sql` | 🟢 Easy | Single-table aggregation (`COUNT`, `SUM`, `AVG`) | 5 |
| `medium_sql` | 🟡 Medium | Multi-table `JOIN` with ranking (`ORDER BY`, `LIMIT`) | 8 |
| `hard_sql` | 🔴 Hard | CTE + window functions (`ROW_NUMBER`, `RANK`, `LAG`) | 10 |

---

## 📊 Baseline Scores

Scores from **Llama-3.1-8B-Instruct** evaluated at environment launch:

| Task | Score | Status |
|---|---|---|
| `easy_sql` | **1.000** | ✅ Solved |
| `medium_sql` | **0.000** | ❌ Unsolved |
| `hard_sql` | **0.000** | ❌ Unsolved |

> The gap between easy and medium/hard tasks reveals a steep difficulty cliff — even capable 8B models struggle with multi-table reasoning and advanced SQL constructs. Can your model do better?

---

## 🗂️ Project Structure

```
openenv-sql-analyst/
│
├── 🐍 Agent & Inference
│   ├── inference.py           ← Agent runner: LLM → SQL → environment loop
│   └── openenv.yaml           ← OpenEnv metadata spec
│
├── 🖥️ server/                 ← Environment server (DB, reset/step endpoints)
│   ├── main.py                ← FastAPI app exposing /reset and /step
│   ├── database.py            ← SQLite e-commerce DB setup
│   └── tasks/                 ← Task definitions (easy, medium, hard)
│
├── 🐳 Dockerfile              ← Production container
├── requirements.txt
├── pyproject.toml
├── uv.lock
└── validate-submission.sh     ← OpenEnv submission validator
```

---

## 🚀 Quick Start

### Option 1 — Docker (Recommended)

```bash
git clone https://github.com/AyushChauhan910/openenv-sql-analyst.git
cd openenv-sql-analyst

docker build -t sql-analyst-env .
docker run -p 7860:7860 sql-analyst-env
```

The environment server will be live at **http://localhost:7860**.

---

### Option 2 — Run the Agent

With the environment running (locally or on HF Spaces), point the agent at it:

```bash
# Against local server
PING_URL=http://localhost:7860 \
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
HF_TOKEN=your_token_here \
python inference.py
```

```bash
# Against HF Spaces deployment
PING_URL=https://ayush0910-openenv-sql-analyst.hf.space \
MODEL_NAME=gpt-4o-mini \
HF_TOKEN=your_token_here \
python inference.py
```

---

## ⚙️ Configuration

All parameters are set via environment variables:

| Variable | Default | Description |
|---|---|---|
| `PING_URL` | HF Spaces URL | URL of the running environment server |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | LLM to use for SQL generation |
| `HF_TOKEN` | *(required)* | HuggingFace API token |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | OpenAI-compatible API base |
| `API_KEY` | Falls back to `HF_TOKEN` | API key override |

---

## 🔄 Agent Loop

```
Environment Reset (task_name)
          │
          ▼
   Observe schema + question
          │
          ▼
   LLM generates SQL query  ◄──────────────────┐
          │                                     │
          ▼                                     │
   POST /step {sql_query}                       │
          │                                     │
          ▼                                     │
   Receive {reward, done, observation}          │
          │                                     │
      reward > 0? ─── No ── refine & retry ─────┘
          │
         Yes
          │
          ▼
      [END] — log score & exit
```

The agent gets **up to N steps** (task-dependent) to arrive at a correct answer. Each incorrect attempt is accompanied by the query result, giving the model a chance to self-correct.

---

## 📝 Log Format

The agent produces structured logs for benchmarking pipelines:

```
[START] task=hard_sql env=sql-analyst-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=SELECT product_id, SUM(...) reward=0.00 done=false error=Missing window function
[STEP] step=2 action=WITH ranked AS (...) SELECT ... reward=1.00 done=true error=null
[END] success=true steps=2 score=1.000 rewards=0.00,1.00
```

---

## 🧑‍💻 API Reference

The environment server exposes two endpoints:

### `POST /reset`

Initializes a new episode for the given task.

```json
Request:  { "task_name": "hard_sql" }
Response: { "schema_info": "...", "question": "...", "step": 0, "done": false }
```

### `POST /step`

Submits a SQL query and receives feedback.

```json
Request:  { "sql_query": "SELECT ..." }
Response: { "reward": 1.0, "done": true, "observation": { ... }, "info": { ... } }
```

---

## 🧪 Submitting to OpenEnv

Validate your submission before pushing:

```bash
bash validate-submission.sh
```

This checks that your environment is correctly structured, the server responds to `/reset` and `/step`, and logs match the required `[START]`/`[STEP]`/`[END]` format.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agent LLM Interface | OpenAI-compatible API (HF Router) |
| LLM Models Supported | Qwen2.5, Llama 3.1, GPT-4o, and any OpenAI-compatible model |
| Environment Server | FastAPI + SQLite |
| Containerization | Docker |
| Hosting | Hugging Face Spaces (Docker SDK) |
| Package Management | `uv` (ultra-fast Python package manager) |

---

## 🙏 Acknowledgements

- [OpenEnv](https://openenv.dev) for the agent evaluation framework
- [Hugging Face](https://huggingface.co) for model hosting and Spaces deployment
- [Qwen Team](https://github.com/QwenLM/Qwen) for the baseline model

---

<div align="center">

*Push the frontier of LLM SQL reasoning — one query at a time.*

**[⭐ Star this repo](https://github.com/AyushChauhan910/openenv-sql-analyst)** &nbsp;·&nbsp; **[🤗 Try on HF Spaces](https://huggingface.co/spaces/ayush0910/openenv-sql-analyst)**

</div>
