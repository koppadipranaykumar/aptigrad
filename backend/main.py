import os
import json
import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import edge_tts
from faster_whisper import WhisperModel

app = FastAPI(title="AptiGrad AI Mock Interview Engine")

# --- CONFIGURATION & MODEL INITIALIZATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# Initialize local Whisper STT on NVIDIA GPU (RTX 3050)
stt_model = WhisperModel("base", device="cpu", compute_type="int8")


# --- HELPER FUNCTIONS FOR AUDIO PIPELINE ---
def transcribe_audio_file(file_path: str) -> str:
    """Converts user audio into text using local Whisper STT on GPU."""
    segments, _ = stt_model.transcribe(file_path, beam_size=5)
    return "".join([segment.text for segment in segments]).strip()

async def synthesize_speech(text: str, output_path: str):
    """Converts AI response text into human-like MP3 speech using Edge-TTS."""
    communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural")
    await communicate.save(output_path)


# --- 1. RESUME & PROFILE ONBOARDING ---
@app.post("/api/v1/onboard")
async def onboard_candidate(
    domain: str = Form(...),
    target_role: str = Form(...),
    resume: UploadFile = File(...)
):
    content = await resume.read()
    resume_text = content.decode("utf-8", errors="ignore")
    
    return {
        "status": "success",
        "message": "Candidate onboarded successfully",
        "session_config": {
            "domain": domain,
            "target_role": target_role,
            "resume_snippet": resume_text[:300]
        }
    }


# --- 2. ADAPTIVE EVALUATION ENGINE ---
def evaluate_and_generate_next(user_answer: str, domain: str, current_q: str, current_diff: str):
    prompt = f"""
    SYSTEM: You are AptiGrad, an expert technical interviewer for {domain}.
    CONTEXT: Current Question: "{current_q}" | Difficulty: {current_diff}
    STUDENT ANSWER: "{user_answer}"
    
    TASK:
    1. Evaluate answer quality on a 0-10 scale.
    2. Determine difficulty change: 'INCREASE', 'DECREASE', or 'MAINTAIN'.
    3. Formulate the EXACT NEXT interview question based on user performance.
    
    Respond STRICTLY in valid JSON format with keys:
    "score" (int), "feedback" (string), "difficulty_change" (string), "next_question" (string).
    """
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "aptigrad-interviewer",
            "prompt": prompt,
            "format": "json",
            "stream": False
        })
        return json.loads(response.json()["response"])
    except Exception as e:
        print(f"Ollama execution error: {e}")
        return {
            "score": 5,
            "feedback": "Processed response.",
            "difficulty_change": "MAINTAIN",
            "next_question": f"Can you elaborate further on {domain} fundamentals?"
        }


# --- 3. VOICE-TO-VOICE INTERVIEW ENDPOINT ---
@app.post("/api/v1/voice-turn")
async def voice_interview_turn(
    audio_file: UploadFile = File(...),
    domain: str = Form(...),
    current_question: str = Form(...),
    current_difficulty: str = Form(...)
):
    session_id = str(uuid.uuid4())
    input_audio_path = os.path.join(TEMP_AUDIO_DIR, f"in_{session_id}.wav")
    output_audio_filename = f"out_{session_id}.mp3"
    output_audio_path = os.path.join(TEMP_AUDIO_DIR, output_audio_filename)

    # 1. Save uploaded user audio chunk
    with open(input_audio_path, "wb") as f:
        f.write(await audio_file.read())

    # 2. Convert User Audio -> Text (STT)
    user_text = transcribe_audio_file(input_audio_path)

    # 3. Evaluate answer & generate next question with Ollama model
    result = evaluate_and_generate_next(
        user_answer=user_text,
        domain=domain,
        current_q=current_question,
        current_diff=current_difficulty
    )

    # 4. State Logic: Adjust Difficulty Level
    diff_levels = ["Easy", "Medium", "Hard"]
    current_idx = diff_levels.index(current_difficulty) if current_difficulty in diff_levels else 1
    
    if result.get("difficulty_change") == "INCREASE" and current_idx < 2:
        new_difficulty = diff_levels[current_idx + 1]
    elif result.get("difficulty_change") == "DECREASE" and current_idx > 0:
        new_difficulty = diff_levels[current_idx - 1]
    else:
        new_difficulty = diff_levels[current_idx]

    # 5. Convert AI Next Question -> Speech Audio (TTS)
    await synthesize_speech(result["next_question"], output_audio_path)

    # Clean up input audio
    if os.path.exists(input_audio_path):
        os.remove(input_audio_path)

    return {
        "user_transcription": user_text,
        "score": result.get("score", 0),
        "feedback": result.get("feedback", ""),
        "next_question": result.get("next_question", ""),
        "new_difficulty": new_difficulty,
        "audio_url": f"/api/v1/audio/{output_audio_filename}"
    }


# --- 4. STREAM AUDIO FILE SERVING ---
@app.get("/api/v1/audio/{filename}")
async def serve_audio_file(filename: str):
    file_path = os.path.join(TEMP_AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")


# --- 5. WEBSOCKET TEXT INTERVIEW STREAM ---
@app.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket):
    await websocket.accept()
    session_data = {
        "difficulty": "Medium",
        "score_history": [],
        "domain": "Software Engineering",
        "current_question": "Explain the difference between process and thread in OS."
    }
    
    # Send First Question to Client
    await websocket.send_json({
        "type": "QUESTION",
        "question": session_data["current_question"],
        "difficulty": session_data["difficulty"]
    })

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_answer = payload.get("answer", "")

            # Process answer with local AI model
            result = evaluate_and_generate_next(
                user_answer=user_answer,
                domain=session_data["domain"],
                current_q=session_data["current_question"],
                current_diff=session_data["difficulty"]
            )

            # Update Session States
            session_data["score_history"].append(result.get("score", 0))
            session_data["current_question"] = result.get("next_question", "")
            
            if result.get("difficulty_change") == "INCREASE" and session_data["difficulty"] == "Easy":
                session_data["difficulty"] = "Medium"
            elif result.get("difficulty_change") == "INCREASE" and session_data["difficulty"] == "Medium":
                session_data["difficulty"] = "Hard"
            elif result.get("difficulty_change") == "DECREASE" and session_data["difficulty"] == "Hard":
                session_data["difficulty"] = "Medium"
            elif result.get("difficulty_change") == "DECREASE" and session_data["difficulty"] == "Medium":
                session_data["difficulty"] = "Easy"

            # Stream response back to Frontend
            await websocket.send_json({
                "type": "EVALUATION_AND_NEXT",
                "feedback": result.get("feedback", ""),
                "score": result.get("score", 0),
                "next_question": result.get("next_question", ""),
                "new_difficulty": session_data["difficulty"]
            })

    except WebSocketDisconnect:
        print("Candidate disconnected from session.")


# --- 6. SCORECARD GENERATOR ---
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
        "summary_feedback": report_data.feedback_list
    }
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)