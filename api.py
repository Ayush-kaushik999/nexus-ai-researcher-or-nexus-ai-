import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(title="Nexus Research AI Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    privacy_mode: bool = True
    use_web_search: bool = False
    provider: str = "ollama"


class AgentResponse(BaseModel):
    summary: str
    details: str
    key_facts: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)


def content_to_text(content: Any) -> str:
    """Normalize LangChain text or content-block responses for the API."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        ]
        return "\n".join(text_parts)
    return str(content)


def execute_research_agent(request: ResearchRequest) -> AgentResponse:
    query = request.query.strip()
    if not query:
        raise ValueError("Please enter a question or request.")

    privacy_mode = request.privacy_mode
    use_web_search = request.use_web_search and not privacy_mode
    provider = "ollama" if privacy_mode else request.provider.lower()
    if provider in {"groq-cloud", "groq_cloud"}:
        provider = "groq"

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        llm = ChatOllama(
            model=model,
            temperature=0,
            num_predict=2000,
            client_kwargs={"timeout": 120},
        )
        model_name = f"Ollama {model}"
    elif provider == "groq":
        from langchain_groq import ChatGroq

        if not os.getenv("GROQ_API_KEY"):
            raise ValueError(
                "Groq is selected, but GROQ_API_KEY is missing from .env. "
                "Add it locally or choose Ollama."
            )

        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        llm = ChatGroq(
            model=model,
            temperature=0,
            timeout=60,
            max_retries=1,
            max_tokens=2000,
        )
        model_name = f"Groq {model}"
    else:
        raise ValueError("provider must be 'ollama' or 'groq'.")

    used_tools = [model_name]
    if use_web_search:
        from langchain.agents import create_agent
        from tools import tools

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are a precise, honest research assistant. "
                "Use web tools for current claims, do not invent facts, and answer the request exactly."
            ),
        )
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        answer = content_to_text(result["messages"][-1].content)
        used_tools.extend(["get_current_datetime", "search_web", "search_wikipedia"])
    else:
        answer = llm.invoke(
            "Answer clearly and completely. Preserve requested formats such as quizzes, essays, lists, or code. "
            f"Do not invent facts.\n\nUser request:\n{query}"
        )
        answer = content_to_text(answer.content)

    return AgentResponse(
        summary="Generated locally or by the selected model.",
        details=answer,
        tools_used=used_tools,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/research", response_model=AgentResponse)
async def research_endpoint(request: ResearchRequest) -> AgentResponse:
    try:
        return await run_in_threadpool(execute_research_agent, request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        if os.getenv("DEBUG", "false").lower() == "true":
            raise
        raise HTTPException(status_code=500, detail="Research request failed.") from error


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")