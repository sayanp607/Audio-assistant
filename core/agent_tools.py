import os
from langchain_core.tools import tool
from core.vector_store import load_vector_store, get_retriever

@tool
def search_meeting_transcript(query: str, session_id: str = "meeting_transcript") -> str:
    """Searches the meeting transcript for specific information, discussions, action items, or quotes.
    Use this tool whenever the user asks questions about what was said or decided in the meeting."""
    try:
        vector_store = load_vector_store(collection_name=session_id)
        retriever = get_retriever(vector_store, k=5)
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant information found in the meeting transcript."
        return "\n\n---\n\n".join([d.page_content for d in docs])
    except Exception as e:
        return f"Error searching meeting transcript: {str(e)}"

@tool
def search_web(query: str) -> str:
    """Searches the internet for real-time information, technical definitions, fact-checking, or background context.
    Use this tool if the required information is NOT found in the meeting transcript or when the user asks general/external questions."""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key and tavily_api_key.strip():
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_api_key.strip())
            response = client.search(query=query, max_results=3)
            results = []
            for r in response.get("results", []):
                results.append(f"Title: {r.get('title')}\nURL: {r.get('url')}\nSnippet: {r.get('content')}")
            if results:
                return "\n\n".join(results)
        except Exception as e:
            print(f"Tavily search error: {e}, falling back to DuckDuckGo...")

    # Fallback to DuckDuckGo Search
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return f"No search results found on the web for: {query}"
            formatted = []
            for r in results:
                formatted.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nLink: {r.get('href')}")
            return "\n\n".join(formatted)
    except Exception as e:
        return f"Error executing web search: {str(e)}"

@tool
def save_action_items_or_notes(content: str, filename: str = "meeting_notes.md") -> str:
    """Saves formatted meeting notes, summaries, action items, or report content to a file on disk.
    Use this tool when the user requests saving, exporting, or writing notes/action items to a document."""
    try:
        os.makedirs("exports", exist_ok=True)
        # Ensure the file goes into exports/ directory
        safe_filename = os.path.basename(filename)
        if not safe_filename.endswith((".md", ".txt")):
            safe_filename += ".md"
        filepath = os.path.join("exports", safe_filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"Successfully saved content to '{filepath}'."
    except Exception as e:
        return f"Error saving file: {str(e)}"
