import os
import re
import json
import requests
import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import edge_tts
from faster_whisper import WhisperModel

app = FastAPI(title="AptiGrad AI Mock Interview Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

stt_model = WhisperModel("base", device="cpu", compute_type="int8")

# Updated Domain Openings
DOMAIN_OPENINGS = {
    "JAVA": "Welcome to your Java interview! To get started, could you explain the internal working of the Java Virtual Machine and how garbage collection operates?",
    "PYTHON": "Welcome to your Python interview! Let me know — how does Python handle dynamic typing, memory management, and GIL (Global Interpreter Lock)?",
    "C": "Welcome to your C programming interview! Let's begin — can you explain how manual memory management works using malloc, calloc, and free, along with potential pointer pitfalls?",
    "C++": "Welcome to your C++ interview! To kick off, could you explain object lifetime, RAII, and the difference between smart pointers like unique_ptr and shared_ptr?",
    "JavaScript": "Welcome to your JavaScript interview! Let's get started — how does the event loop execute asynchronous code, microtasks, and macrotasks under the hood?",
    "DBMS": "Welcome to your Database Systems interview! To start off, could you explain normalization and walk me through why it matters when designing a relational schema?",
    "Computer Networks": "Welcome to your Computer Networks interview! Can you walk me through what happens step by step when you type a URL into your browser?",
    "Operating Systems": "Welcome to your Operating Systems interview! Could you explain the difference between a process and a thread, and when you'd choose one over the other?",
    "DSA": "Welcome to your Data Structures and Algorithms interview! To get started, walk me through how you analyze time and space complexity using Big-O notation, and how you select an optimal data structure for a given problem."
}

INTERVIEWER_SYSTEM_PROMPT = """You are AptiGrad, an expert adaptive technical interviewer.

STRICT DOMAIN BOUNDARY RULE:
You MUST ask questions ONLY related to the specified domain. 
- If the domain is 'DSA', ask strictly about data structures (Trees, Graphs, Arrays, Linked Lists, Hash Tables) and algorithms (Sorting, Searching, Dynamic Programming, Complexity). Do NOT ask language-specific syntax questions.
- If the domain is 'JAVA', 'PYTHON', 'C', 'C++', or 'JavaScript', ask strictly about language runtime, syntax, memory models, and core language paradigms.

Your job is to evaluate the candidate's answer, provide brief constructive feedback, and ask the next follow-up question.

You must:
1. Evaluate technical correctness and depth.
2. Provide a 1-2 sentence feedback snippet on the candidate's answer.
3. Adapt difficulty based on the candidate's answer.
4. Ask exactly ONE technical follow-up question strictly within the chosen domain.
5. Return ONLY valid JSON matching this schema:

{
  "score": 0-10,
  "difficulty_change": "INCREASE" | "DECREASE" | "MAINTAIN",
  "feedback": "Short feedback on what the candidate did well or missed.",
  "next_question": "..."
}
"""

BANNED_PHRASES = [
    "good foundation",
    "let's build the foundation first",
    "basic concept behind this topic in your own words",
    "explain the main trade-offs, edge cases, and production considerations"
]

def transcribe_audio_file(file_path: str) -> str:
    try:
        segments, _ = stt_model.transcribe(file_path, beam_size=5)
        text = "".join([segment.text for segment in segments]).strip()
        print(f"[STT Transcript]: '{text}'")
        return text
    except Exception as e:
        print(f"[STT Error]: {e}")
        return ""

async def synthesize_speech(text: str, output_path: str):
    try:
        communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural")
        await communicate.save(output_path)
        print(f"[TTS Success]: Speech saved to {output_path}")
    except Exception as e:
        print(f"[TTS Error]: {e}")

def extract_json_safely(raw_text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except Exception as e:
        print(f"[JSON Parser Warning]: {e}")
        return {}

OPENING_AUDIO_CACHE: dict[str, str] = {}

def _safe_filename(domain: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', domain.strip())

@app.on_event("startup")
async def pregenerate_opening_audio():
    for domain_name, opening_text in DOMAIN_OPENINGS.items():
        filename = f"opening_{_safe_filename(domain_name)}.mp3"
        filepath = os.path.join(TEMP_AUDIO_DIR, filename)
        try:
            await synthesize_speech(opening_text, filepath)
            OPENING_AUDIO_CACHE[domain_name] = filename
            print(f"[Startup Cache]: Pre-generated opening audio for '{domain_name}'")
        except Exception as e:
            print(f"[Startup Cache Error]: Failed to pre-generate audio for '{domain_name}': {e}")

@app.post("/api/v1/start-interview")
async def start_interview(domain: str = Form(...)):
    opening_text = DOMAIN_OPENINGS.get(domain, f"Welcome to your {domain} interview! Tell me about your background in {domain}.")
    cached_filename = OPENING_AUDIO_CACHE.get(domain)
    
    if cached_filename and os.path.exists(os.path.join(TEMP_AUDIO_DIR, cached_filename)):
        output_audio_filename = cached_filename
    else:
        session_id = str(uuid.uuid4())
        output_audio_filename = f"out_start_{session_id}.mp3"
        output_audio_path = os.path.join(TEMP_AUDIO_DIR, output_audio_filename)
        await synthesize_speech(opening_text, output_audio_path)

    return {
        "question_text": opening_text,
        "audio_url": f"/api/v1/audio/{output_audio_filename}",
        "hidden_difficulty": "Medium",
        "question_count": 1,
        "is_complete": False
    }

def ask_ollama_direct(domain: str, current_q: str, user_answer: str, current_diff: str, used_questions: list[str]) -> dict:
    user_content = (
        f"Domain: {domain}\n"
        f"Current Difficulty: {current_diff}\n"
        f"Question: {current_q}\n"
        f"Candidate Answer: {user_answer}\n"
        f"STRICT INSTRUCTION: Ask a question strictly about {domain}."
    )

    messages = [
        {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

    payload = {
        "model": "aptigrad-interviewer",
        "messages": messages,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }

    for attempt in range(1, 4):
        try:
            res = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=90)
            res_json = res.json()
            raw_text = res_json.get("message", {}).get("content", "").strip()

            if not raw_text:
                continue

            parsed = extract_json_safely(raw_text)
            candidate_q = parsed.get("next_question", "").strip()
            is_banned = any(phrase in candidate_q.lower() for phrase in BANNED_PHRASES)

            if len(candidate_q) > 10 and candidate_q != current_q and candidate_q not in used_questions and not is_banned:
                return parsed

            payload["messages"].append({"role": "assistant", "content": raw_text})
            payload["messages"].append({
                "role": "user",
                "content": f"Do NOT ask generic questions. Ask a specific, brand new technical question strictly about {domain}."
            })

        except Exception as e:
            print(f"[Ollama Call Exception] attempt {attempt}: {e}")

    return {}

def evaluate_and_generate_next(
    user_answer: str, 
    domain: str, 
    current_q: str, 
    current_diff: str, 
    question_count: int = 1,
    used_questions: list[str] = None
):
    if used_questions is None:
        used_questions = []

    if question_count >= 25:
        return {
            "score": 8,
            "difficulty_change": "MAINTAIN",
            "feedback": "Great job completing the interview!",
            "next_question": "That concludes our mock interview for today. Excellent work!",
            "is_complete": True,
            "is_reasking": False
        }

    if not user_answer or len(user_answer.strip()) < 3:
        return {
            "score": 0,
            "difficulty_change": "MAINTAIN",
            "feedback": "Answer was too brief or uncaptured.",
            "next_question": f"I didn't capture your full response. Could you please clarify your answer regarding: {current_q}?",
            "is_complete": False,
            "is_reasking": True
        }

    ollama_res = ask_ollama_direct(domain, current_q, user_answer, current_diff, used_questions)
    next_question_text = ollama_res.get("next_question", "").strip()

    if "<" in next_question_text or "strictly about" in next_question_text:
        next_question_text = next_question_text.replace("<", "").replace(">", "").strip()

    if not next_question_text:
        return {
            "score": ollama_res.get("score", 5),
            "difficulty_change": ollama_res.get("difficulty_change", "MAINTAIN"),
            "feedback": "Clear explanation, let's go deeper.",
            "next_question": f"Could you elaborate further on core concepts within {domain}?",
            "is_complete": False,
            "is_reasking": True
        }

    return {
        "score": ollama_res.get("score", 7),
        "difficulty_change": ollama_res.get("difficulty_change", "MAINTAIN"),
        "feedback": ollama_res.get("feedback", "Good explanation."),
        "next_question": next_question_text,
        "is_complete": False,
        "is_reasking": False
    }

@app.post("/api/v1/voice-turn")
async def voice_interview_turn(
    audio_file: UploadFile = File(...),
    domain: str = Form(...),
    current_question: str = Form(...),
    current_difficulty: str = Form(...),
    question_count: int = Form(...),
    used_questions_json: str = Form("[]")
):
    session_id = str(uuid.uuid4())
    input_audio_path = os.path.join(TEMP_AUDIO_DIR, f"in_{session_id}.wav")
    output_audio_filename = f"out_{session_id}.mp3"
    output_audio_path = os.path.join(TEMP_AUDIO_DIR, output_audio_filename)

    with open(input_audio_path, "wb") as f:
        f.write(await audio_file.read())

    user_text = transcribe_audio_file(input_audio_path)

    try:
        used_questions = json.loads(used_questions_json)
    except Exception:
        used_questions = []

    result = evaluate_and_generate_next(
        user_answer=user_text,
        domain=domain,
        current_q=current_question,
        current_diff=current_difficulty,
        question_count=question_count,
        used_questions=used_questions
    )

    diff_levels = ["Easy", "Medium", "Hard"]
    current_idx = diff_levels.index(current_difficulty) if current_difficulty in diff_levels else 1
    
    if result.get("difficulty_change") == "INCREASE" and current_idx < 2:
        new_difficulty = diff_levels[current_idx + 1]
    elif result.get("difficulty_change") == "DECREASE" and current_idx > 0:
        new_difficulty = diff_levels[current_idx - 1]
    else:
        new_difficulty = diff_levels[current_idx]

    await synthesize_speech(result["next_question"], output_audio_path)

    if os.path.exists(input_audio_path):
        os.remove(input_audio_path)

    is_reasking = result.get("is_reasking", False)
    next_count = question_count if is_reasking else question_count + 1

    return {
        "question_text": result["next_question"],
        "feedback": result.get("feedback", ""),
        "score": result.get("score", 7),
        "audio_url": f"/api/v1/audio/{output_audio_filename}",
        "hidden_difficulty": new_difficulty,
        "question_count": next_count,
        "is_complete": result["is_complete"]
    }

@app.get("/api/v1/audio/{filename}")
async def serve_audio_file(filename: str):
    file_path = os.path.join(TEMP_AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")

class FinalReportRequest(BaseModel):
    scores: list[int]
    feedback_list: list[str]

@app.post("/api/v1/generate-scorecard")
def generate_scorecard(report_data: FinalReportRequest):
    avg_score = sum(report_data.scores) / max(len(report_data.scores), 1)
    return {
        "overall_score": round(avg_score, 1),
        "total_questions_answered": len(report_data.scores),
        "performance_rating": "Strong Hire" if avg_score >= 7.5 else "Needs Practice",
        "detailed_feedback": report_data.feedback_list
    }