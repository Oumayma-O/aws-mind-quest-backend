# Langfuse Integration Guide for AWS Mind Quest

## Changes Made

### 1. ✅ Dependencies Added
- `langfuse==2.60.10` added to `requirements.txt`
- Includes `langfuse.decorators.observe` and `langfuse.langchain.CallbackHandler`

### 2. ✅ Environment Variables Configured
Already set in `.env`:
```bash
LANGFUSE_SECRET_KEY = "sk-lf-66745017-e131-4b1b-82a5-64e05e91725e"
LANGFUSE_PUBLIC_KEY = "pk-lf-6a85eac2-157f-45f7-8bf1-610684de1a62"
LANGFUSE_HOST = "https://cloud.langfuse.com"
```

### 3. ✅ Observability Module Created
File: `app/utils/observability.py` - Provides shared Langfuse handler

### 4. 🔧 Required Code Changes

#### A. Update `app/services/quiz_generator.py`

**Line 8-9**: Replace imports
```python
# OLD:
from langchain_core.output_parsers import PydanticOutputParser
from app.utils.observability import langfuse_handler
import os

# NEW:
from langchain_core.output_parsers import PydanticOutputParser
from langfuse.decorators import observe
from langfuse.langchain import CallbackHandler
import os
```

**Lines 33-40**: Replace LangSmith setup with Langfuse
```python
# OLD:
    def __init__(self, db: Session):
        self.db = db
        
        # Enable LangSmith tracing if configured
        if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
            logger.info(f"LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")

# NEW:
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize Langfuse handler for LangChain tracing
        self.langfuse_handler = CallbackHandler()
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            logger.info("Langfuse tracing enabled for quiz generation")
```

**Line 95**: Add @observe decorator before generate_quiz
```python
# OLD:
    async def generate_quiz(

# NEW:
    @observe(name="generate_quiz")
    async def generate_quiz(
```

**Line 211**: Update chain.invoke to include Langfuse callback
```python
# OLD:
        quiz_response: QuizResponse = chain.invoke(invoke_params)

# NEW:
        # Invoke chain with Langfuse callback handler
        quiz_response: QuizResponse = chain.invoke(
            invoke_params,
            config={"callbacks": [self.langfuse_handler]}
        )
```

### 5. 🐳 Update `docker-compose.yml`

Add to the `api` service environment section (around line 33):
```yaml
    environment:
      DATABASE_URL: postgresql://admin:password@db:5432/aws_mind_quest
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o-mini}
      # ... existing vars ...
      
      # Langfuse Cloud Tracing
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
      LANGFUSE_HOST: ${LANGFUSE_HOST:-https://cloud.langfuse.com}
```

## How to Use

### 1. Apply Code Changes
Make the 4 code changes above to `quiz_generator.py`

### 2. Rebuild Docker
```pwsh
docker-compose down
docker-compose build
docker-compose up -d
```

### 3. Verify Tracing
1. Generate a quiz via the API
2. Go to https://cloud.langfuse.com
3. Select your project
4. View traces under "Runs" tab

### 4. What Gets Traced
- **Decorated function**: `generate_quiz` method (user_id, certification_id, difficulty)
- **LangChain chain**: Prompt → LLM → Parser pipeline
- **LLM calls**: Model, tokens, latency, cost
- **Metadata**: Certification name, domains, difficulty level

## Example Trace Structure
```
generate_quiz (root span)
  ├── Prompt Template (input)
  ├── ChatOpenAI (gpt-4o-mini)
  │   ├── Token usage
  │   ├── Cost
  │   └── Latency
  ├── PydanticOutputParser (output)
  └── Quiz saved (result)
```

## Troubleshooting

### No traces appearing?
1. Check env vars are loaded: `docker-compose exec api env | grep LANGFUSE`
2. Verify keys in Langfuse dashboard
3. Check logs: `docker-compose logs api | grep -i langfuse`

### Traces incomplete?
- Ensure `CallbackHandler()` is passed to `chain.invoke(..., config={"callbacks": [...]})`
- Check Python decorator is `@observe()` not `@traceable()`

## Next Steps

Optional enhancements:
1. Add `propagate_attributes(tags=[...], metadata={...})` for richer traces
2. Trace `retrieval_service.retrieve_with_compression()` separately
3. Add user feedback correlation via Langfuse scores
4. Set up alerts for high latency/cost in Langfuse dashboard

## References
- Langfuse Python SDK: https://langfuse.com/docs/sdk/python
- LangChain Integration: https://langfuse.com/docs/integrations/langchain/tracing
- Decorator Guide: https://langfuse.com/docs/sdk/python/decorators
