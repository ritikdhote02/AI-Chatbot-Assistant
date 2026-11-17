import logging

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch

logger = logging.getLogger(__name__)
load_dotenv()


@tool
def search_web(query: str) -> str:
    """
    Search the internet for current information.

    Use this tool for latest news, recent events,
    current software versions, and recent developments.
    """
    try:
        tavily = TavilySearch(
            max_results=5,
            topic="general",
            search_depth="basic",
            include_answer=False,
            include_raw_content=False,
        )

        result = tavily.invoke({"query": query})

        search_results = result.get("results", [])

        if not search_results:
            return "No relevant web search results were found."

        formatted_results = []

        for index, item in enumerate(search_results, start=1):
            formatted_results.append(
                f"Source {index}\n"
                f"Title: {item.get('title', 'No title')}\n"
                f"URL: {item.get('url', 'No URL')}\n"
                f"Content: {item.get('content', 'No content')}"
            )

        return "\n\n".join(formatted_results)

    except Exception:
        logger.exception("Internet search failed.")
        return (
            "Internet search is currently unavailable. "
            "Do not invent search results. Inform the user "
            "that the search could not be completed."
        )
