from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question
from utils.translator import translate_long_text
def run_pipeline(source: str, input_lang: str = "english", output_lang: str = "english") -> dict:
    print("starting AI Video Assistant")

    chunks = process_input(source)

    english_transcript = transcribe_all(chunks, input_lang)
    
    # Translate raw transcript if needed
    raw_transcript = translate_long_text(english_transcript, output_lang)
    print(f"raw transcription (first 300 characters ) {raw_transcript[:300]}...")
    
    # Save the full transcript to a text file so the user can read it
    with open("full_transcript.txt", "w", encoding="utf-8") as f:
        f.write(raw_transcript)
    print("\n[✔] Full translated transcript saved to 'full_transcript.txt' so you can read it!")

    title = generate_title(english_transcript, output_lang)

    summary = summarize(english_transcript, output_lang)

    action_item = extract_action_items(english_transcript, output_lang)

    decisions = extract_key_decisions(english_transcript, output_lang)
    questions = extract_questions(english_transcript, output_lang)
    
    rag_chain = build_rag_chain(english_transcript)

    return {
        "title": title,
        "transcript": raw_transcript,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
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

    # Phase 2 — Chat with your meeting via RAG
    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n🤖 Assistant: {answer}\n")