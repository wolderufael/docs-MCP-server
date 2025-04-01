from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
from bs4 import BeautifulSoup
load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL="https://google.serper.dev/search"

docs_urls = {
    "langchain": "python.langchain.com/docs",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
}

async def search_web(query: str) -> dict | None:
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}
        
async def fetch_url(url: str):
  async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            return text
        except httpx.TimeoutException:
            return "Timeout error"


@mcp.tool()  
async def get_docs(query: str, library: str):
    """
Search the latest documentation for a specific library and query.

Parameters:
    query: The search term or phrase to look up in the documentation.
        Examples:
        - "how to use Chroma DB"
        - "RAG implementation"
        - "chat model parameters"
        - "embedding functions"

    library: The name of the library to search within.
        Must be one of: "langchain", "llama-index", or "openai"
        Examples:
        - "langchain" - searches python.langchain.com/docs
        - "llama-index" - searches docs.llamaindex.ai
        - "openai" - searches platform.openai.com/docs

Returns:
    str: The relevant documentation text found for the query.
        Returns "No results found" if no matches are found.

Raises:
    ValueError: If the specified library is not supported.
"""
    if library not in docs_urls:
        raise ValueError(f"Library {library} not supported by this tool")
    
    query = f"site:{docs_urls[library]} {query}"
    results = await search_web(query)
    if len(results["organic"]) == 0:
        return "No results found"
    
    text = ""
    for result in results["organic"]:
        text += await fetch_url(result["link"])
    return text


if __name__ == "__main__":
    mcp.run(transport="stdio")