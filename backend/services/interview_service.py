import json
from openai import OpenAI
from models.interview import EvaluationResult, NextQuestion

client = OpenAI(api_key="YOUR_API_KEY") # Or local Ollama endpoint

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

def process_interview_turn(user_answer: str, current_question: str, domain: str, current_level_idx: int):
    # Step 1: Grade the User's Answer
    eval_prompt = f"""
    Domain: {domain}
    Difficulty Level: {DIFFICULTY_LEVELS[current_level_idx]}
    Question Asked: {current_question}
    Student Answer: {user_answer}
    
    Evaluate the student's answer objectively. Determine if difficulty should INCREASE, DECREASE, or MAINTAIN.
    """
    
    # Force structured output returning EvaluationResult schema
    eval_response = client.beta.chat.completions.parse(
        model="gpt-4o-mini", # or local model formatted to JSON
        messages=[{"role": "user", "content": eval_prompt}],
        response_format=EvaluationResult
    )
    
    evaluation = eval_response.choices[0].message.parsed

    # Step 2: Python Code Manages the State / Difficulty Transition
    new_level_idx = current_level_idx
    if evaluation.difficulty_change == "INCREASE" and current_level_idx < 2:
        new_level_idx += 1
    elif evaluation.difficulty_change == "DECREASE" and current_level_idx > 0:
        new_level_idx -= 1

    # Step 3: Generate Next Question Based on New Difficulty Level
    next_q_prompt = f"""
    Domain: {domain}
    Target Difficulty: {DIFFICULTY_LEVELS[new_level_idx]}
    Previous Question: {current_question}
    Student's Previous Answer Performance: {evaluation.score}/10
    
    Ask EXACTLY ONE follow-up or new conceptual interview question corresponding strictly to {DIFFICULTY_LEVELS[new_level_idx]} level. Do not output conversational filler.
    """

    next_q_response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": next_q_prompt}],
        response_format=NextQuestion
    )
    
    next_question = next_q_response.choices[0].message.parsed
    
    return {
        "evaluation": evaluation,
        "next_question": next_question,
        "new_difficulty_idx": new_level_idx
    }