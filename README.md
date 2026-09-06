# Nexus AI — Autonomous Research Suite 🤖

Nexus AI is an agentic AI research platform designed to bridge local privacy with real-time web intelligence. It features a dual-engine execution router that seamlessly switches between a 100% offline local privacy shield powered by **Ollama (Llama 3.2)** and live, online agentic search powered by **LangChain** and **Groq**.

![Nexus AI Interface Preview](assets/app_preview.png)

---

## 📽️ Live Demonstration

![Nexus AI Execution Demo](assets/demo.gif)

*14-second demonstration showcasing dual-mode execution (Local Privacy Shield vs. Live Web Search Agent).*

---

## ✨ Key Features

- **Dual-Engine Execution Router:**
  - **Local Privacy Mode:** Routes queries to locally running Ollama (`llama3.2`) models—ensuring zero data leaves your local machine.
  - **Live Web Research Mode:** Leverages LangChain agents integrated with DuckDuckGo and Wikipedia tools to synthesize up-to-date web intelligence beyond LLM knowledge cutoffs.
- **Strict Output Validation:** Uses **Pydantic** schemas to strictly enforce JSON response structures for summary generation.
- **Async Backend:** Built on **FastAPI** for high-concurrency request handling and responsive query streaming.
- **Modern UI:** Built with a clean, responsive glassmorphism aesthetic.

---

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI (Python 3.10+)
- **Agentic Orchestration:** LangChain, LangChain Community
- **Local Model Provider:** Ollama (Llama 3.2)
- **Cloud LLM Provider:** Groq
- **Data Validation:** Pydantic v2
- **Search Integrations:** DuckDuckGo Search, Wikipedia API

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have the following installed:
- Python 3.10 or higher
- [Ollama](https://ollama.com/) (with `llama3.2` pulled: `ollama pull llama3.2`)

### 2. Installation & Setup

Clone the repository and set up your virtual environment:

```bash
git clone [https://github.com/YOUR_USERNAME/nexus-ai-researcher.git](https://github.com/YOUR_USERNAME/nexus-ai-researcher.git)
cd nexus-ai-researcher

python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
