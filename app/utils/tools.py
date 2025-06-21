from crewai.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults, TavilySearchResults
from typing import Type
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

class DuckDuckGoSearchInput(BaseModel):
    """Input schema for DuckDuckGo search."""
    query: str = Field(..., description="Search query to look up")

class TavilySearchInput(BaseModel):
    """Input schema for Tavily search."""
    query: str = Field(..., description="Search query to look up")

class DuckDuckGoSearchTool(BaseTool):
    name: str = "duckduckgo_search"
    description: str = (
        "Search the web using DuckDuckGo. "
        "Useful for finding current information, news, and general web content. "
        "Input should be a search query string."
    )
    args_schema: Type[BaseModel] = DuckDuckGoSearchInput

    def _run(self, query: str) -> str:
        """Execute the search and return results."""
        try:
            search = DuckDuckGoSearchResults(num_results=5)
            results = search.invoke(query)
            
            if not results:
                return "No results found for the given query."
            
            # Format results for better readability
            formatted_results = []
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    link = result.get('link', 'No link')
                    snippet = result.get('snippet', 'No description')
                    formatted_results.append(f"{i}. **{title}**\n   Link: {link}\n   Description: {snippet}\n")
                else:
                    formatted_results.append(f"{i}. {str(result)}\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error performing DuckDuckGo search: {str(e)}"

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = (
        "Search the web using Tavily Search API. "
        "Provides high-quality search results with AI-powered summarization. "
        "Useful for research, current events, and detailed information gathering. "
        "Input should be a search query string."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(self, query: str) -> str:
        """Execute the Tavily search and return results."""
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                return "Tavily API key not found. Please set TAVILY_API_KEY environment variable."
            
            search = TavilySearchResults(
                max_results=5,
                api_wrapper_kwargs={"api_key": tavily_api_key}
            )
            results = search.invoke(query)
            
            if not results:
                return "No results found for the given query."
            
            # Format results for better readability
            formatted_results = []
            for i, result in enumerate(results, 1):
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    url = result.get('url', 'No URL')
                    content = result.get('content', 'No content available')
                    formatted_results.append(f"{i}. **{title}**\n   URL: {url}\n   Content: {content}\n")
                else:
                    formatted_results.append(f"{i}. {str(result)}\n")
            
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Error performing Tavily search: {str(e)}"

# Create instances of the tools
duckduckgo_tool = DuckDuckGoSearchTool()
tavily_tool = TavilySearchTool()