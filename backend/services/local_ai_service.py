import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

# Extended timeout (120s) prevents Ollama read timeout errors
HTTP_TIMEOUT = httpx.Timeout(120.0, connect=10.0)

async def generate_domain_opening(domain: str) -> dict:
    prompt = f"""
    You are AptiGrad, a senior technical interviewer conducting a mock interview strictly for the '{domain}' domain.
    Generate a warm greeting and an initial, entry-level opening question specific to {domain}.
    
    Return ONLY a JSON object with this key:
    {{
        "question_text": "<your dynamic domain opening question>"
    }}
    """
    
    payload = {
        "model": "aptigrad-interviewer",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        res_json = response.json()
        result = json.loads(res_json.get("response", "{}"))
        
        # Integrate your local Text-To-Speech (TTS) generation call here to return audio_url
        audio_url = "/api/v1/audio/opening_sample.mp3" 
        result["audio_url"] = audio_url
        return result

async def process_voice_turn(domain: str, current_question: str, candidate_answer: str, current_difficulty: str) -> dict:
    prompt = f"""
    SYSTEM: You are AptiGrad, a senior technical interviewer. 
    STRICT CONSTRAINT: You are interviewing for the '{domain}' domain ONLY. Do NOT deviate to other fields.
    
    Context:
    - Domain: {domain}
    - Current Difficulty: {current_difficulty}
    - Previous Question: {current_question}
    - Candidate Answer: {candidate_answer}
    
    Evaluate the candidate's response. Adjust difficulty accordingly (INCREASE, DECREASE, or MAINTAIN).
    Generate a follow-up technical question strictly within the '{domain}' domain.
    
    Return ONLY a JSON object with this structure:
    {{
        "score": <0-10 integer>,
        "difficulty_adjustment": "<INCREASE|DECREASE|MAINTAIN>",
        "hidden_difficulty": "<Easy|Medium|Hard>",
        "question_text": "<next domain-specific question>"
    }}
    """

    payload = {
        "model": "aptigrad-interviewer",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.post(OLLAMA_URL, json=payload)
        res_json = response.json()
        return json.loads(res_json.get("response", "{}"))