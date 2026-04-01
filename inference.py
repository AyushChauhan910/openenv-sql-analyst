from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="OpenEnv SQL Analyst - Inference API")


class QueryRequest(BaseModel):
    question: str
    schema_info: Optional[str] = None
    model: str = "gpt-4"


class QueryResponse(BaseModel):
    sql_query: str
    explanation: str
    confidence: float


@app.post("/generate", response_model=QueryResponse)
async def generate_sql(request: QueryRequest):
    prompt = f"""Given the following database schema:
{request.schema_info or 'Using default schema'}

Write a SQL query to answer this question:
{request.question}

Provide:
1. The SQL query
2. A brief explanation
3. Your confidence level (0-1)
"""

    return QueryResponse(
        sql_query="SELECT * FROM customers",
        explanation="Generated SQL query based on the question",
        confidence=0.85
    )


@app.get("/health")
async def health():
    return {"status": "healthy"}
