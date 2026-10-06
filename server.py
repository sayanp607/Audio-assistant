import uuid
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all, transcribe_all_native
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, load_rag_chain, ask_question
from core.agent import run_agent
from utils.translator import translate_long_text

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Video Assistant & Agent API")

# Add CORS so React / React Native can talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    source: str
    input_lang: str = "english"
    output_lang: str = "english"

class ChatRequest(BaseModel):
    session_id: str
    question: str
    use_agent: bool = True
    chat_history: Optional[List[Dict[str, str]]] = None

@app.post("/process-video")
def process_video(req: ProcessRequest):
    session_id = str(uuid.uuid4())
    print(f"Starting pipeline for session: {session_id}")
    
    try:
        chunks = process_input(req.source)
        english_transcript = transcribe_all(chunks, req.input_lang)
        
        # For the displayed transcript: if input != english, get native script directly
        if req.input_lang.lower() != "english":
            native_transcript = transcribe_all_native(chunks, language=req.input_lang)
        else:
            native_transcript = english_transcript

        # Further translate native transcript if user wants a different output language
        if req.output_lang.lower() not in [req.input_lang.lower(), "english"]:
            raw_transcript = translate_long_text(native_transcript, req.output_lang)
        else:
            raw_transcript = native_transcript
        
        title = generate_title(english_transcript, req.output_lang)
        summary = summarize(english_transcript, req.output_lang)
        action_item = extract_action_items(english_transcript, req.output_lang)
        decisions = extract_key_decisions(english_transcript, req.output_lang)
        questions = extract_questions(english_transcript, req.output_lang)
        
        # Build Vector Store for RAG & Agent with this session_id
        build_rag_chain(english_transcript, session_id=session_id)
        
        return {
            "session_id": session_id,
            "title": title,
            "transcript": raw_transcript,
            "summary": summary,
            "action_items": action_item,
            "key_decisions": decisions,
            "open_questions": questions
        }
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(req: ChatRequest):
    """Chat endpoint supporting both Agentic tool-calling reasoning and standard RAG."""
    try:
        if req.use_agent:
            result = run_agent(
                session_id=req.session_id,
                user_message=req.question,
                chat_history=req.chat_history
            )
            return {
                "answer": result["answer"],
                "tools_used": result["tools_used"],
                "agentic": True
            }
        else:
            rag_chain = load_rag_chain(session_id=req.session_id)
            answer = ask_question(rag_chain, req.question)
            return {"answer": answer, "tools_used": [], "agentic": False}
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent-chat")
def agent_chat(req: ChatRequest):
    """Explicit Agentic chat endpoint with tool executions."""
    try:
        result = run_agent(
            session_id=req.session_id,
            user_message=req.question,
            chat_history=req.chat_history
        )
        return result
    except Exception as e:
        print(f"Error in agent chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
