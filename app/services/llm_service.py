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
    """Base model for quiz questions"""
    question_text: str = Field(..., description="The quiz question text")
    question_type: str = Field(..., description="Type: multiple_choice, multi_select, or true_false")
    options: List[str] = Field(..., description="List of answer options")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, or hard")
    domain: str = Field(..., description="AWS domain/topic (e.g., 'S3', 'EC2', 'IAM')")
    explanation: str = Field(..., description="Educational explanation for the answer")


class MultipleChoiceQuestion(QuestionBase):
    """Single choice question"""
    correct_answer: str = Field(..., description="The single correct answer")


class MultiSelectQuestion(QuestionBase):
    """Multi-select question"""
    correct_answer: List[str] = Field(..., description="List of correct answers")


class TrueFalseQuestion(QuestionBase):
    """True/False question"""
    correct_answer: str = Field(..., description="Either 'True' or 'False'")


class QuizResponse(BaseModel):
    """Structured response containing generated quiz questions"""
    questions: List[Union[MultipleChoiceQuestion, MultiSelectQuestion, TrueFalseQuestion]] = Field(
        ..., 
        description="List of generated quiz questions"
    )



class LLMService:
    """Service for interacting with OpenAI API using LangChain"""
    
    def __init__(self):
        """Initialize LangChain ChatOpenAI client"""
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
        focus_domains: List[str]
    ) -> PromptTemplate:
        """
        Create a LangChain prompt template for quiz generation
        
        Args:
            certification: Certification name
            difficulty: Difficulty level
            focus_domains: List of domains to focus on
            
        Returns:
            PromptTemplate object
        """
        domains_text = ", ".join(focus_domains) if focus_domains else "General AWS topics"
        
        format_instructions = self.parser.get_format_instructions()
        
        template = f"""You are an expert AWS certification instructor. Generate exactly 5 quiz questions for {{certification}} at {{difficulty}} difficulty level.

FOCUS PRIMARILY ON THESE DOMAINS: {{focus_domains}}

Generate a mix of:
- 3 multiple choice questions (single answer only)
- 1 multi-select question (multiple correct answers)
- 1 true/false question

For each question, ensure:
- The question is practical and reflects real AWS scenarios
- Options are plausible and realistic
- The explanation is detailed and educational
- The domain accurately reflects the AWS service/topic

{format_instructions}

Important guidelines:
- All questions must be at the specified difficulty level
- Options must be valid and realistic
- Correct answers must be clear and unambiguous
- Explanations should educate the learner"""

        return PromptTemplate(
            input_variables=["certification", "difficulty", "focus_domains"],
            template=template
        )
    
    async def generate_quiz(
        self,
        certification: str,
        difficulty: str,
        focus_domains: List[str],
        num_questions: int = 5
    ) -> QuizResponse:
        """
        Generate AWS quiz questions using OpenAI with structured output
        
        Args:
            certification: Certification name (e.g., "AWS Solutions Architect")
            difficulty: Difficulty level (easy, medium, hard)
            focus_domains: List of domains to focus on
            num_questions: Number of questions to generate (default: 5)
            
        Returns:
            QuizResponse object with structured questions
            
        Raises:
            ValueError: If LLM fails to generate valid structured output
        """
        try:
            # Create prompt template
            prompt = self._create_prompt(certification, difficulty, focus_domains)
            
            # Create LangChain chain: Prompt -> LLM -> Parser
            chain = prompt | self.llm | self.parser
            
            logger.info(f"Generating {num_questions} questions for {certification} ({difficulty})")
            
            # Invoke chain with input variables
            quiz_response = chain.invoke({
                "certification": certification,
                "difficulty": difficulty,
                "focus_domains": ", ".join(focus_domains) if focus_domains else "General AWS topics"
            })
            
            # Parse and validate with Pydantic
            result = QuizResponse(**quiz_response)
            
            logger.info(f"Successfully generated {len(result.questions)} questions for {certification}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error in quiz generation: {e}")
            raise ValueError(f"Failed to generate valid quiz: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating quiz with LangChain: {e}", exc_info=True)
            raise
