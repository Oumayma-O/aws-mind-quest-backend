"""OpenAI LLM service for quiz generation"""

import json
import logging
from typing import List, Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_quiz(
        self,
        certification: str,
        difficulty: str,
        focus_domains: List[str]
    ) -> dict:
        """
        Generate AWS quiz questions using OpenAI
        
        Args:
            certification: Certification name (e.g., "AWS Cloud Practitioner")
            difficulty: Difficulty level (easy, medium, hard)
            focus_domains: List of domains to focus on
            
        Returns:
            Dictionary with generated questions
        """
        
        domains_text = ", ".join(focus_domains) if focus_domains else "General AWS topics"
        
        prompt = f"""You are an expert AWS certification instructor. Generate exactly 5 quiz questions for {certification} at {difficulty} difficulty level.

FOCUS PRIMARILY ON THESE DOMAINS: {domains_text}

Generate a mix of:
- 3 multiple choice questions (single answer)
- 1 multi-select question (multiple correct answers)
- 1 true/false question

For each question, ensure:
- The question is practical and realistic
- Options are plausible
- The explanation is educational and detailed

Return ONLY valid JSON in this exact format (NO markdown, NO code blocks, NO extra text):
{{
  "questions": [
    {{
      "question_text": "What is the primary purpose of AWS IAM?",
      "question_type": "multiple_choice",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Detailed explanation of why this is correct...",
      "difficulty": "{difficulty}",
      "domain": "IAM"
    }},
    {{
      "question_text": "Which of the following are features of S3?",
      "question_type": "multi_select",
      "options": ["Feature A", "Feature B", "Feature C", "Feature D"],
      "correct_answer": ["Feature A", "Feature C"],
      "explanation": "S3 provides Features A and C...",
      "difficulty": "{difficulty}",
      "domain": "S3"
    }},
    {{
      "question_text": "EC2 instances are serverless compute resources.",
      "question_type": "true_false",
      "options": ["True", "False"],
      "correct_answer": "False",
      "explanation": "EC2 instances are managed servers, not serverless...",
      "difficulty": "{difficulty}",
      "domain": "EC2"
    }}
  ]
}}

IMPORTANT: Return ONLY the JSON object, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AWS certification quiz generator. You MUST return valid JSON only, with no markdown formatting or extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract response content
            content = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            # Parse JSON
            quiz_data = json.loads(content)
            
            logger.info(f"Successfully generated {len(quiz_data.get('questions', []))} questions for {certification}")
            return quiz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response content: {content}")
            raise ValueError("LLM returned invalid JSON format")
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise
