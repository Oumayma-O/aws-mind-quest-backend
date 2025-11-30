"""Lambda handler wrapper for AWS Lambda deployment"""

from mangum import Mangum
from app.main import app

# Wrap FastAPI app for Lambda
# This handler is used when deploying to AWS Lambda
handler = Mangum(app, lifespan="off")
