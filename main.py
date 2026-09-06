import os
import sys
import traceback
from typing import cast

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class ResearchResponse(BaseModel):
	summary: str = Field(
		description="A short 1-2 sentence overview of what was generated"
	)
	details: str = Field(
		description="The complete generated response, including full quizzes, detailed answers, code, or essays, in markdown"
	)
	key_facts: list[str] = Field(
		default_factory=list,
		description="Relevant key takeaways or bullet points; use only as many as the question needs"
	)


def main() -> None:
	query = input("What can I help you with? ").strip()
	if not query:
		raise ValueError("Please enter a question or request.")
	if len(query) > 1000:
		raise ValueError("Please keep your question under 1,000 characters.")
	privacy_mode = os.getenv("PRIVACY_MODE", "true").lower() == "true"
	use_web_search = (
		not privacy_mode
		and os.getenv("USE_WEB_SEARCH", "false").lower() == "true"
	)
	provider = os.getenv("MODEL_PROVIDER", "ollama").lower()

	if privacy_mode:
		provider = "ollama"
	if provider == "groq":
		from langchain_groq import ChatGroq

		llm = ChatGroq(
			model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
			temperature=0,
			timeout=60,
			max_retries=1,
			max_tokens=2000,
		)
		model_name = f"Groq {os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')}"
	elif provider == "ollama":
		from langchain_ollama import ChatOllama

		llm = ChatOllama(
			model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
			temperature=0,
			num_predict=2000,
			client_kwargs={"timeout": 120},
		)
		model_name = f"Ollama {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}"
	else:
		raise ValueError("MODEL_PROVIDER must be 'ollama' or 'groq'.")

	if use_web_search:
		from langchain.agents import create_agent
		from tools import tools

		print("\n> Entering agent execution chain...")
		agent = create_agent(
			model=llm,
			tools=tools,
			system_prompt=(
				"You are a precise, honest research assistant. "
				"Answer only what the user asks, follow the requested format, and do not flatter or agree just to please the user. "
				"Use the available web tools for current or time-sensitive claims. "
				"Do not invent facts; clearly state when information is uncertain or unavailable."
			),
		)
		used_tools = [
			model_name,
			"get_current_datetime",
			"DuckDuckGoSearchRun",
			"WikipediaQueryRun",
		]
		result = agent.invoke({
			"messages": [{"role": "user", "content": query}]
		})
		research_answer = result["messages"][-1].content
	else:
		if privacy_mode:
			print("\n> Privacy mode enabled; query will not be sent to web tools.")
		else:
			print("\n> Web search disabled; using the language model directly...")
		used_tools = [model_name]
		research_answer = llm.invoke(
			"Answer the user's request clearly and completely. Preserve requested formats such as quizzes, essays, lists, or code. "
			"Do not invent facts; state uncertainty when needed.\n\n"
			f"User request:\n{query}"
		).content

	# A second JSON-formatting generation is slow and unreliable on llama3.2:3b.
	# Keep local/privacy mode to one generation and preserve its complete answer.
	if provider == "ollama" and not use_web_search:
		print("\n--- FINAL RESEARCH RESULTS ---")
		print("Tools used:", ", ".join(used_tools))
		print("\n--- FULL RESPONSE ---")
		print(research_answer)
		return

	structured_llm = llm.with_structured_output(
		ResearchResponse,
		method="json_mode",
	)
	format_request = (
		"Return valid JSON matching the schema with summary, details, and key_facts. "
		"Put the complete generated response in details, preserving all requested questions, answers, code, or essay content verbatim. "
		"Do not summarize or omit details. Use no more than 5 key_facts. "
		"Do not add filler, praise, speculation, or unsupported claims. If information is uncertain or current data is unavailable, say so.\n\n"
		f"Original question: {query}"
	)
	format_request += f"\n\nGenerated answer:\n{research_answer}"
	structured_response = cast(ResearchResponse, structured_llm.invoke(format_request))

	print("\n--- FINAL RESEARCH RESULTS ---")
	print("Tools used:", ", ".join(used_tools))
	print(f"\n--- SUMMARY ---\n{structured_response.summary}")
	print(f"\n--- FULL RESPONSE ---\n{structured_response.details}")
	if structured_response.key_facts:
		print("\n--- KEY TAKEAWAYS ---")
		for fact in structured_response.key_facts[:5]:
			print(f"- {fact}")


if __name__ == "__main__":
	try:
		main()
	except Exception as error:
		error_text = str(error).lower()
		if "connection" in error_text or "ollama" in error_text:
			advice = "Make sure the Ollama app is running and llama3.2:3b is installed."
		elif "model_not_found" in error_text or "does not exist" in error_text:
			advice = "Check that the selected model is available to your Groq account."
		elif "timeout" in error_text or "timed out" in error_text:
			advice = "Check your internet connection or increase the model timeout."
		elif "ddgs" in error_text or "dns" in error_text or "search" in error_text:
			advice = "Disable web search with USE_WEB_SEARCH=false or check your network."
		elif "json" in error_text or "structured" in error_text:
			advice = "Check the model's structured-output support and the ResearchResponse schema."
		else:
			advice = "Run again with DEBUG=true for the full traceback."

		print(f"\n[ERROR] {type(error).__name__}: {error}")
		print(f"[ACTION] {advice}")
		if os.getenv("DEBUG", "false").lower() == "true":
			traceback.print_exc()
		sys.exit(1)
