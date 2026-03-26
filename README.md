# 🤖 Autonomous AI Research Agent (Full-Stack)

🚀 **Live Demo:** [https://ai-research-agent-alpha-orpin.vercel.app/](https://ai-research-agent-alpha-orpin.vercel.app/)

A production-ready, full-stack AI application featuring an autonomous research agent. Built with modern, asynchronous architecture to handle LLM latency, complex state management, and seamless client-server communication.

## 🏛️ Architecture & Engineering Decisions

This project is not a simple "API wrapper." It demonstrates a decoupled, scalable architecture designed with specific trade-offs in mind:

* **Orchestration (LangGraph):** Chose LangGraph over traditional linear chains (like standard LangChain) to enable cyclical, stateful agent workflows. The agent possesses "memory" via Checkpointers and autonomously decides when to use external tools (DuckDuckGo Web Search) versus its internal reasoning.
* **Backend (FastAPI):** Selected for its native asynchronous capabilities (`async`/`await`). AI tool calling and LLM generation are high-latency I/O operations; FastAPI ensures the server remains non-blocking and performant. 
* **Data Validation (Pydantic):** Strict type hinting and validation for API contracts between the frontend and backend.
* **Frontend (Vite + React + TypeScript):** Opted for a Single Page Application (SPA) approach using Vite instead of an SSR framework like Next.js. Since the chat interface is highly interactive and doesn't require SEO indexing, a decoupled React client interacting directly with the FastAPI backend minimizes operational complexity.
* **Styling (Tailwind CSS v4):** Utilized the new zero-config Oxide engine of Tailwind v4 for rapid, utility-first UI development, maintaining a clean, minimalist, and professional SaaS aesthetic.
* **Package Management (uv & pnpm):** Implemented `uv` for lightning-fast Python dependency management and `pnpm` for Node.js to prevent "phantom dependencies" and optimize disk space via symlinking.

## 🛠️ Tech Stack

* **AI Engine:** OpenAI GPT-4o, LiteLLM, LangGraph, LangChain Core
* **Backend:** Python 3, FastAPI, Uvicorn
* **Frontend:** TypeScript, React, Vite
* **Styling:** Tailwind CSS v4

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
uv sync # Install dependencies
# Create a .env file and add your OPENAI_API_KEY
uv run uvicorn server:app --reload --port 8001