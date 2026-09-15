from fastapi import APIRouter, HTTPException, Form
from services.local_ai_service import generate_domain_opening, process_voice_turn

router = APIRouter(prefix="/api/v1", tags=["Interview"])

@router.post("/start-interview")
async def start_interview(domain: str = Form(...)):
    """
    Generates a dynamic, domain-specific opening question directly from the model.
    """
    try:
        opening_data = await generate_domain_opening(domain)
        return {
            "question_text": opening_data.get("question_text"),
            "hidden_difficulty": "Medium",
            "question_count": 1,
            "audio_url": opening_data.get("audio_url", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))