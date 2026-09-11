from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    is_correct: bool = Field(description="True if student's answer is accurate and sufficient.")
    score: int = Field(description="Score out of 10 for the response quality.")
    feedback: str = Field(description="Brief direct feedback on the student's answer.")
    difficulty_change: str = Field(description="Options: 'INCREASE', 'DECREASE', 'MAINTAIN'")

class NextQuestion(BaseModel):
    question: str = Field(description="The next targeted interview question.")
    target_difficulty: str = Field(description="Current question level: Easy, Medium, or Hard.")