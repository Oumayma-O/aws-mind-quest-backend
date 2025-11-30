import logging
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.quizz_pydantic_models import QuizResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.config import settings
from app.database.models import Quiz, Question, Certification

logger = logging.getLogger(__name__)

AWS_DOMAINS = [
    "IAM", "EC2", "S3", "VPC", "RDS",
    "Lambda", "CloudWatch", "CloudFormation",
    "Security and Compliance", "Pricing and Support"
]


class QuizGeneratorService:
    """Service for generating quizzes directly using LangChain + OpenAI"""

    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            max_tokens=2000
        )
        self.parser = PydanticOutputParser(pydantic_object=QuizResponse)

    def _create_prompt(self, certification: str, difficulty: str, domains: List[str]) -> PromptTemplate:
        domains_text = ", ".join(domains) if domains else "General AWS Topics"
        format_instructions = self.parser.get_format_instructions()
        template = f"""
You are an expert AWS certification instructor.
Generate exactly 5 quiz questions for {{certification}} at {{difficulty}} difficulty level.

FOCUS PRIMARILY ON THESE AWS DOMAINS:
{domains_text}

Generate a mix of:
- 3 multiple choice questions (single correct answer)
- 1 multi-select question (multiple correct answers)
- 1 true/false question

For each question:
- Make it realistic and AWS scenario-based
- Ensure options are plausible
- Provide a clear correct answer
- Include a detailed educational explanation
- Assign a correct AWS domain (e.g., EC2, IAM, VPC)

{format_instructions}
"""
        return PromptTemplate(
            input_variables=["certification", "difficulty","domains_text"],
            template=template
        )

    async def generate_quiz(
        self,
        user_id: UUID,
        certification_id: UUID,
        difficulty: str,
        weak_domains: Optional[List[Dict[str, str]]] = None
    ) -> Quiz:
        # Fetch certification
        certification = self.db.query(Certification).filter(Certification.id == certification_id).first()
        if not certification:
            raise ValueError("Certification not found")

        # Determine focus domains
        if weak_domains:
            focus_domains = [d["name"] for d in weak_domains[:3]]
        else:
            focus_domains = AWS_DOMAINS[:3]

        logger.info(f"Generating quiz for user {user_id} | Domains: {focus_domains}")

        # Build prompt and chain
        prompt = self._create_prompt(certification.name, difficulty, focus_domains)
        chain = prompt | self.llm | self.parser

        quiz_response: QuizResponse = chain.invoke({
            "certification": certification.name,
            "difficulty": difficulty
        })

        # Save quiz
        quiz = Quiz(
            user_id=user_id,
            certification_id=certification_id,
            difficulty=difficulty,
            total_questions=len(quiz_response.questions)
        )
        self.db.add(quiz)
        self.db.flush()

        # Save questions using Pydantic models
        for q in quiz_response.questions:
            question = Question(
                quiz_id=quiz.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                difficulty=q.difficulty,
                domain=q.domain
            )
            self.db.add(question)

        self.db.commit()
        self.db.refresh(quiz)
        logger.info(f"Quiz {quiz.id} generated with {len(quiz_response.questions)} questions")

        return quiz
