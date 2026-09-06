from datetime import datetime

import wikipedia
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


@tool
def get_current_datetime() -> str:
	"""Return the current local date and time."""
	return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


search_tool = DuckDuckGoSearchRun()
wikipedia_tool = WikipediaQueryRun(
	api_wrapper=WikipediaAPIWrapper(wiki_client=wikipedia)
)


@tool("search_web")
def safe_web_search(query: str) -> str:
	"""Search the web and return results, or a clear unavailable message."""
	try:
		return search_tool.run(query)
	except Exception as error:
		return f"Web search unavailable: {type(error).__name__}. Use another source or answer cautiously."


@tool("search_wikipedia")
def safe_wikipedia_search(query: str) -> str:
	"""Search Wikipedia and return results, or a clear unavailable message."""
	try:
		return wikipedia_tool.run(query)
	except Exception as error:
		return f"Wikipedia unavailable: {type(error).__name__}. Continue without Wikipedia."


tools = [get_current_datetime, safe_web_search, safe_wikipedia_search]
