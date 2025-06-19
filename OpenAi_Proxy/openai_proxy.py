"""
Advanced OpenAI Proxy Server (FastAPI)

This server acts as a secure proxy between clients and the OpenAI API.
It exposes a POST /ask endpoint that accepts a question and user_id,
calls the OpenAI API using the API key from the environment, and returns the answer.
"""

from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import openai
import os
import time
from collections import defaultdict

# Configuration 
ALLOWED_ORIGINS = ["*"]  # domain for the production
ALLOWED_MODELS = {"gpt-3.5-turbo", "gpt-4"}
API_AUTH_KEY = os.getenv("PROXY_AUTH_KEY", "dev-secret")  # this is to be set in the production
RATE_LIMIT = 10  #  To limit requests per minute per user_id

# Main Setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Rate Limiting to protect from abuse
user_requests = defaultdict(list)  # user_id -> [timestamps]

def is_rate_limited(user_id: str) -> bool:
    now = time.time()
    window = 60  # seconds
    requests = user_requests[user_id]
    # Removing the Old Requests
    user_requests[user_id] = [t for t in requests if now - t < window]
    if len(user_requests[user_id]) >= RATE_LIMIT:
        return True
    user_requests[user_id].append(now)
    return False

# Response Models
class AskRequest(BaseModel):
    question: str
    user_id: Optional[str] = "anonymous"
    model: Optional[str] = "gpt-3.5-turbo"

class AskResponse(BaseModel):
    answer: Optional[str] = None
    error: Optional[str] = None

# End Points
@app.post("/ask", response_model=AskResponse)
async def ask_openai(
    req: AskRequest,
    x_api_key: str = Header(None)
):
    """
    Accepts a JSON payload with 'question', optional 'user_id', and optional 'model'.
    Requires X-API-KEY header for authentication.
    Enforces rate limiting per user_id.
    Restricts model selection to allowed models.
    Calls OpenAI's ChatCompletion API and returns the answer.
    """
    # Authenticating the API KEY
    if x_api_key != API_AUTH_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

    # Rate Limit
    if is_rate_limited(req.user_id):
        return AskResponse(error="Rate limit exceeded. Please wait and try again.")

    # Restricting Model
    model = req.model if req.model in ALLOWED_MODELS else "gpt-3.5-turbo"

    # Calling OpenAi
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": req.question}],
            max_tokens=256,
            temperature=0.7,
        )
        answer = response.choices[0].message["content"]
        return AskResponse(answer=answer)
    except Exception as e:
        return AskResponse(error=str(e)) 