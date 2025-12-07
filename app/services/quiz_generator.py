import logging
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.quizz_pydantic_models import QuizResponse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langfuse.decorators import observe
from langfuse.callback import CallbackHandler
import os
import time
from decimal import Decimal

from app.config import settings
from app.database.models import Quiz, Question, Certification, CertificationDocument
from app.services.vector_store import vector_store
from app.services.embedding_service import embedding_service
from app.services.document_processor import document_processor
from app.services.retrieval_service import retrieval_service
from datetime import datetime

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
        
        # Initialize Langfuse callback handler
        self.langfuse_handler = CallbackHandler()
        logger.info("Langfuse tracing initialized for quiz generation")
        
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            max_completion_tokens=2000  # Changed from max_tokens for newer models
        )
        self.parser = PydanticOutputParser(pydantic_object=QuizResponse)

    def _create_prompt(self, certification: str, difficulty: str, domains: List[str], context: str = "") -> PromptTemplate:
        format_instructions = self.parser.get_format_instructions()
        # Escape curly braces in format_instructions by doubling them
        format_instructions_escaped = format_instructions.replace("{", "{{").replace("}", "}}")
        
        context_section = ""
        if context:
            context_section = (
                "\n\nUSE THE FOLLOWING OFFICIAL CERTIFICATION CONTENT AS YOUR PRIMARY SOURCE:\n"
                "===== CERTIFICATION EXAM GUIDE CONTENT =====\n"
                "{context}\n"
                "===== END OF CONTENT =====\n\n"
                "Base your questions DIRECTLY on the content above. "
                "Questions should test understanding of the specific topics, services, and concepts mentioned.\n"
            )
        
        template = (
            "You are an expert AWS certification instructor.\n"
            "Generate exactly 5 quiz questions for {certification} at {difficulty} difficulty level.\n\n"
            f"{context_section}"
            "FOCUS PRIMARILY ON THESE AWS DOMAINS:\n"
            "{domains}\n\n"
            "Generate a mix of:\n"
            "- 3 multiple choice questions (single correct answer)\n"
            "- 1 multi-select question (MUST have 2 or more correct answers, NOT just 1,and don't mention (select two)per example in the question text)\n"
            "- 1 true/false question\n\n"
            "For each question:\n"
            "- Make it realistic and AWS scenario-based\n"
            "- Ensure options are plausible\n"
            "- Provide a clear correct answer\n"
            "- Include a detailed educational explanation\n"
            "- Assign a correct AWS domain (e.g., EC2, IAM, VPC)\n\n"
            f"{format_instructions_escaped}"
        )
        
        input_vars = ["certification", "difficulty", "domains"]
        if context:
            input_vars.append("context")
        
        return PromptTemplate(
            input_variables=input_vars,
            template=template
        )

    @observe(name="generate_quiz")
    async def generate_quiz(
        self,
        user_id: UUID,
        certification_id: UUID,
        difficulty: str,
        weak_domains: Optional[List[str]] = None
    ) -> Quiz:
        # Fetch certification
        certification = self.db.query(Certification).filter(Certification.id == certification_id).first()
        if not certification:
            raise ValueError("Certification not found")
        
        # Check if documents exist and are processed
        documents = self.db.query(CertificationDocument).filter(
            CertificationDocument.certification_id == certification_id
        ).all()
        
        if documents:
            # Check if any documents need processing
            unprocessed = [doc for doc in documents if doc.processing_status != "completed"]
            
            if unprocessed:
                logger.info(f"Found {len(unprocessed)} unprocessed documents. Processing before quiz generation...")
                
                for doc in unprocessed:
                    try:
                        # Update status
                        doc.processing_status = "processing"
                        self.db.commit()
                        
                        logger.info(f"Processing document {doc.filename}")
                        
                        # Process document
                        chunks = document_processor.process_document(
                            url=doc.uri,
                            certification_id=str(certification_id),
                            document_id=str(doc.id)
                        )
                        
                        # Generate embeddings
                        chunk_texts = [chunk.text for chunk in chunks]
                        embeddings = embedding_service.embed_texts(chunk_texts)
                        
                        # Store in vector database
                        chunk_data = [
                            {"text": chunk.text, "metadata": chunk.metadata}
                            for chunk in chunks
                        ]
                        vector_store.upsert_chunks(str(certification_id), chunk_data, embeddings)
                        
                        # Update status
                        doc.processing_status = "completed"
                        doc.processed_at = datetime.utcnow()
                        self.db.commit()
                        
                        logger.info(f"Successfully processed document {doc.filename}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process document {doc.filename}: {e}")
                        doc.processing_status = "failed"
                        self.db.commit()

        # Determine focus domains
        if weak_domains:
            focus_domains = weak_domains[:3]
        else:
            focus_domains = AWS_DOMAINS[:3]

        logger.info(f"Generating quiz for user {user_id} | Domains: {focus_domains}")

        # Retrieve relevant context from vector store with randomization
        context = ""
        try:
            if vector_store.collection_exists(certification_id):
                # Create search query from domains
                query_text = f"AWS {certification.name} exam questions about {', '.join(focus_domains)}"
                
                # Use randomized retrieval for diversity across quizzes
                chunks = retrieval_service.retrieve_with_randomization(
                    certification_id=certification_id,
                    query=query_text,
                    top_k=10
                )
                
                if chunks:
                    context = "\n\n".join([f"[Source: Page {c['metadata']['page_number']}]\n{c['text']}" for c in chunks])
                    logger.info(f"Retrieved {len(chunks)} compressed chunks from vector store")
                    
                    # Log document previews for debugging/monitoring
                    logger.info("=== Retrieved Document Previews (Compressed) ===")
                    for i, chunk in enumerate(chunks[:5], 1):  # Log first 5 chunks
                        preview = chunk['text'][:200].replace('\n', ' ')
                        score = chunk.get('score', 'N/A')
                        page = chunk['metadata'].get('page_number', 'N/A')
                        logger.info(f"  Chunk {i} [Page {page}, Score: {score}]: {preview}...")
                    logger.info("=== End Previews ===")
                else:
                    logger.warning("No chunks retrieved from vector store")
            else:
                logger.warning(f"Vector collection does not exist for certification {certification_id}")
        except Exception as e:
            logger.error(f"Failed to retrieve context from vector store: {e}")
            # Continue without context

        # Build prompt and chain
        prompt = self._create_prompt(certification.name, difficulty, focus_domains, context)
        chain = prompt | self.llm | self.parser

        invoke_params = {
            "certification": str(certification.name),
            "difficulty": str(difficulty),
            "domains": ", ".join(focus_domains)
        }
        if context:
            invoke_params["context"] = context

        # Track generation time
        start_time = time.time()
        quiz_response: QuizResponse = chain.invoke(
            invoke_params,
            config={"callbacks": [self.langfuse_handler]}
        )
        generation_time_seconds = time.time() - start_time

        # Save quiz with generation metrics
        quiz = Quiz(
            user_id=user_id,
            certification_id=certification_id,
            difficulty=difficulty,
            total_questions=len(quiz_response.questions),
            generation_time_seconds=Decimal(str(round(generation_time_seconds, 2))),
            llm_model=settings.OPENAI_MODEL
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
