from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain
from core.agent import run_agent
from utils.translator import translate_long_text

def run_pipeline(source: str, input_lang: str = "english", output_lang: str = "english") -> dict:
    print("Starting AI Video & Meeting Assistant...")

    chunks = process_input(source)

    english_transcript = transcribe_all(chunks, input_lang)
    
    # Translate raw transcript if needed
    raw_transcript = translate_long_text(english_transcript, output_lang)
    print(f"\nRaw transcription (first 300 characters):\n{raw_transcript[:300]}...")
    
    # Save the full transcript to a text file so the user can read it
    with open("full_transcript.txt", "w", encoding="utf-8") as f:
        f.write(raw_transcript)
    print("\n[✔] Full translated transcript saved to 'full_transcript.txt'!")

    title = generate_title(english_transcript, output_lang)
    summary = summarize(english_transcript, output_lang)
    action_item = extract_action_items(english_transcript, output_lang)
    decisions = extract_key_decisions(english_transcript, output_lang)
    questions = extract_questions(english_transcript, output_lang)
    
    # Build Chroma Vector Store
    build_rag_chain(english_transcript, session_id="meeting_transcript")

    return {
        "title": title,
        "transcript": raw_transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "session_id": "meeting_transcript"
    }

if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    input_lang = input("Language of the video (e.g., hindi, bengali, english): ").strip() or "english"
    output_lang = input("Language you want to read/chat in (e.g., hindi, bengali, english): ").strip() or "english"
    result = run_pipeline(source, input_lang, output_lang)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_items']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    print(f"\n❓ Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Interactive Agentic Chat
    print("\n💬 Chat with your Agentic Meeting Assistant (type 'exit' to quit)")
    print("💡 The Agent can search transcript, search the web, and save action items.\n")
    
    chat_history = []
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
            
        res = run_agent(session_id="meeting_transcript", user_message=question, chat_history=chat_history)
        
        # Display tools used if any
        if res.get("tools_used"):
            tools_list = ", ".join([t["tool"] for t in res["tools_used"]])
            print(f"⚙️ [Agent Tools Used: {tools_list}]")
            
        print(f"\n🤖 Assistant: {res['answer']}\n")
        
        # Keep short conversation history
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": res["answer"]})