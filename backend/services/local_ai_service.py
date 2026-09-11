import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_aptigrad_model(user_answer: str, domain: str, current_q: str, difficulty: str):
    prompt = f"Domain: {domain} | Difficulty: {difficulty} | Question: {current_q} | Answer: {user_answer}"
    
    payload = {
        "model": "aptigrad-interviewer",
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(OLLAMA_URL, json=payload)
    return response.json().get("response")