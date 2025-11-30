from typing import List, Union
from pydantic import BaseModel
from app.database.enums import Difficulty, QuestionType


class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType
    options: List[str]
    difficulty: Difficulty
    domain: str
    explanation: str


class MultipleChoiceQuestion(QuestionBase):
    correct_answer: str


class MultiSelectQuestion(QuestionBase):
    correct_answer: List[str]


class TrueFalseQuestion(QuestionBase):
    correct_answer: str


class QuizResponse(BaseModel):
    questions: List[Union[
        MultipleChoiceQuestion,
        MultiSelectQuestion,
        TrueFalseQuestion
    ]]
