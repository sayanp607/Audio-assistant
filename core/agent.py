import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from core.agent_tools import search_meeting_transcript, search_web, save_action_items_or_notes

SYSTEM_PROMPT_TEMPLATE = """You are an intelligent, proactive AI Meeting and Video Assistant with Agentic reasoning capabilities.

You have access to the following tools:
1. `search_meeting_transcript(query)`: Search the current meeting/video transcript in the vector database.
2. `search_web(query)`: Search the live internet for external facts, definitions, updates, or topics not covered in the transcript.
3. `save_action_items_or_notes(content, filename)`: Save structured action items, meeting minutes, or reports directly to a file in the exports/ directory.

GUIDELINES FOR REASONING & TOOL CALLING:
- If the user asks about what was said, discussed, or decided in the meeting/video, always use `search_meeting_transcript` first with session_id: "{session_id}".
- If the information is not in the transcript, or if the user asks for background information, fact-checking, or general knowledge, use `search_web`.
- If the user asks to export, save, or write down notes/action items, use `save_action_items_or_notes`.
- Always respond in the EXACT SAME LANGUAGE as the user's question (e.g., English, Bengali, Hindi, etc.).
- Be concise, accurate, and transparent about your findings.
"""

def get_agent_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2,
    )

def build_meeting_agent(session_id: str = "meeting_transcript"):
    """Builds a LangGraph ReAct agent equipped with meeting search, web search, and note saving tools."""
    llm = get_agent_llm()
    tools = [search_meeting_transcript, search_web, save_action_items_or_notes]
    
    system_message = SYSTEM_PROMPT_TEMPLATE.format(session_id=session_id)
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_message
    )
    return agent

def run_agent(session_id: str, user_message: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Runs the ReAct agent on a user message and returns the final answer along with tool execution logs."""
    try:
        agent = build_meeting_agent(session_id=session_id)
        
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))
                    
        messages.append(HumanMessage(content=user_message))
        
        result = agent.invoke({"messages": messages})
        
        # Extract final answer and tool calls made
        final_message = result["messages"][-1]
        final_answer = final_message.content if hasattr(final_message, "content") else str(final_message)
        
        # Track tools used
        tools_used = []
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tools_used.append({
                        "tool": tc.get("name"),
                        "args": tc.get("args")
                    })
                    
        return {
            "answer": final_answer,
            "tools_used": tools_used,
            "session_id": session_id
        }
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "rate_limited" in err_msg.lower():
            err_msg = "Rate limit reached from LLM provider. Please wait a moment and try again."
        return {
            "answer": f"Agent Error: {err_msg}",
            "tools_used": [],
            "session_id": session_id
        }

