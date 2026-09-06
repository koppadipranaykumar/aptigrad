import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

app = FastAPI()

sessions: dict[str, dict] = {}


class Domain(str, Enum):
    dsa = "dsa"
    java = "java"
    web_dev = "web_dev"
    behavioral = "behavioral"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class SessionStatus(str, Enum):
    created = "created"
    in_progress = "in_progress"
    completed = "completed"


class CreateSessionRequest(BaseModel):
    domain: Domain
    student_name: str


class ViolationRequest(BaseModel):
    type: str
    timestamp: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer_text: str


def _generate_question_text(domain: str, difficulty: str, previous_questions: list[str]) -> str:
    system_prompt = (
        f"You are an interview question generator for a mock interview platform. "
        f"Generate exactly ONE interview question for the '{domain}' domain at '{difficulty}' difficulty. "
        f"Return ONLY the question text — no preamble, no numbering, no quotes."
    )
    user_content = "Generate the question now."
    if previous_questions:
        avoided = "\n".join(f"- {q}" for q in previous_questions)
        user_content = f"Avoid repeating or closely resembling these already-asked questions:\n{avoided}"

    try:
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Question generation failed: {str(e)}")


def _grade_answer(domain: str, difficulty: str, question_text: str, answer_text: str) -> dict:
    if domain == Domain.behavioral:
        rubric = (
            "Score the answer 1-5 using the STAR method: does it describe a clear Situation, "
            "Task, Action, and Result? Deduct points for vagueness or missing structure."
        )
    else:
        rubric = (
            "Score the answer 1-5 on technical correctness, clarity, and completeness for the "
            "given difficulty level. A 5 is fully correct and well-explained; a 1 is incorrect or empty."
        )

    system_prompt = (
        "You are grading a mock interview answer. "
        f"{rubric} "
        'Respond with ONLY valid JSON in this exact shape, no other text: '
        '{"score": <integer 1-5>, "reasoning": "<one or two sentence explanation>"}'
    )
    user_content = f"Question ({difficulty}): {question_text}\n\nCandidate's answer: {answer_text}"

    try:
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = message.content[0].text.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        return {"score": int(parsed["score"]), "reasoning": parsed["reasoning"]}
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"Grading response could not be parsed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Grading failed: {str(e)}")


def _maybe_adjust_difficulty(session: dict, score: int):
    order = [Difficulty.easy, Difficulty.medium, Difficulty.hard]
    idx = order.index(session["current_difficulty"])
    if score >= 4 and idx < len(order) - 1:
        session["current_difficulty"] = order[idx + 1]
    elif score <= 2 and idx > 0:
        session["current_difficulty"] = order[idx - 1]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/session")
def create_session(req: CreateSessionRequest):
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "student_name": req.student_name,
        "domain": req.domain,
        "status": SessionStatus.created,
        "current_difficulty": Difficulty.easy,
        "questions": [],
        "violations": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    return sessions[session_id]


@app.get("/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/session/{session_id}/start")
def start_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["status"] = SessionStatus.in_progress
    return session


@app.post("/session/{session_id}/question")
def generate_question(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != SessionStatus.in_progress:
        raise HTTPException(status_code=400, detail="Session is not in progress — call /start first")

    previous = [q["text"] for q in session["questions"]]
    question_text = _generate_question_text(
        domain=session["domain"],
        difficulty=session["current_difficulty"],
        previous_questions=previous,
    )
    question = {
        "id": str(uuid.uuid4()),
        "text": question_text,
        "difficulty": session["current_difficulty"],
        "domain": session["domain"],
        "answer": None,
    }
    session["questions"].append(question)
    return question


@app.post("/session/{session_id}/answer")
def submit_answer(session_id: str, req: SubmitAnswerRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question = next((q for q in session["questions"] if q["id"] == req.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in this session")

    grading = _grade_answer(
        domain=question["domain"],
        difficulty=question["difficulty"],
        question_text=question["text"],
        answer_text=req.answer_text,
    )

    result = {
        "question_id": req.question_id,
        "answer_text": req.answer_text,
        "score": grading["score"],
        "reasoning": grading["reasoning"],
    }
    question["answer"] = result
    _maybe_adjust_difficulty(session, grading["score"])
    return result


@app.post("/session/{session_id}/violation")
def log_violation(session_id: str, violation: ViolationRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["violations"].append({
        "type": violation.type,
        "timestamp": violation.timestamp or datetime.utcnow().isoformat(),
    })
    return {"logged": True, "total_violations": len(session["violations"])}