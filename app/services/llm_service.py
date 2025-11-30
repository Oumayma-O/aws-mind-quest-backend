"""OpenAI LLM service for quiz generation using LangChain"""

import logging
from typing import List, Union
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from app.config import settings

logger = logging.getLogger(__name__)


class QuestionBase(BaseModel):
    question_text: str
    question_type: str
    options: List[str]
    difficulty: str
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



class LLMService:
    """Service for interacting with OpenAI API using LangChain"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            max_tokens=2000
        )
        self.parser = JsonOutputParser(pydantic_object=QuizResponse)

    def _create_prompt(
        self,
        certification: str,
        difficulty: str,
        domains_text: str
    ) -> PromptTemplate:

        format_instructions = self.parser.get_format_instructions()

        template = f"""
You are an expert AWS certification instructor.
Generate exactly 5 quiz questions for {{certification}} at {{difficulty}} difficulty level.

FOCUS PRIMARILY ON THESE AWS DOMAINS:
{{domains_text}}

Generate a mix of:
- 3 multiple choice questions (single correct answer)
- 1 multi-select question (multiple correct answers)
- 1 true/false question

For each question:
- Make it realistic and based on AWS scenario-based learning
- Ensure options are plausible
- Provide a clear correct answer
- Include a detailed educational explanation
- Assign a correct AWS domain (e.g., EC2, IAM, VPC)

{format_instructions}

Important:
- All questions must match the difficulty level
- Avoid ambiguous or trick questions
- Ensure answers are unambiguous and correct
"""

        return PromptTemplate(
            input_variables=["certification", "difficulty", "domains_text"],
            template=template
        )

    async def generate_quiz(
        self,
        certification: str,
        difficulty: str,
        focus_domains: List[str],
        num_questions: int = 5
    ) -> QuizResponse:

        try:
            domains_text = ", ".join(focus_domains) if focus_domains else "General AWS Topics"

            prompt = self._create_prompt(certification, difficulty, domains_text)

            chain = prompt | self.llm | self.parser

            logger.info(f"Generating {num_questions} questions for {certification} ({difficulty}) | Domains: {domains_text}")

            quiz_response = chain.invoke({
                "certification": certification,
                "difficulty": difficulty,
                "domains_text": domains_text
            })

            result = QuizResponse(**quiz_response)

            logger.info(f"Generated {len(result.questions)} questions successfully.")
            return result

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise ValueError(f"Failed to generate valid quiz: {str(e)}")

        except Exception as e:
            logger.error(f"LLM generation error: {e}", exc_info=True)
            raise
