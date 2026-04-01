import os
import requests
import json
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-5-nano")
PING_URL = os.environ.get("PING_URL", "http://localhost:7860")

TASKS = ["easy_sql", "medium_sql", "hard_sql"]
MAX_RETRIES = 3


def get_observation(endpoint):
    r = requests.post(f"{PING_URL}/reset", json={"task_name": endpoint})
    return r.json()


def step(sql_query):
    r = requests.post(f"{PING_URL}/step", json={"sql_query": sql_query})
    return r.json()


def generate_sql(question, schema_info, feedback=None):
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    prompt = f"""You are a SQL expert. Given the following database schema:

{schema_info}

Write a SQL query to answer this question:
{question}

Rules:
- Return ONLY the SQL query, no explanation
- Use standard SQLite syntax
- The query must be a SELECT statement
- Round floats to 2 decimals using ROUND()
"""

    if feedback:
        prompt += f"\nYour previous query had issues: {feedback}\nPlease fix and try again."

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0
    )

    sql = response.choices[0].message.content.strip()

    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    sql = sql.strip().rstrip(";")

    return sql


def run_task(task_name):
    obs = get_observation(task_name)
    question = obs["question"]
    schema_info = obs["schema_info"]

    last_feedback = None

    for attempt in range(MAX_RETRIES):
        sql_query = generate_sql(question, schema_info, last_feedback)
        result = step(sql_query)

        score = result["reward"]
        done = result["done"]
        feedback = result["info"]["feedback"]

        print(f"  Attempt {attempt + 1}: score={score:.2f} | {feedback[:60]}")

        if done or score >= 1.0:
            return score

        last_feedback = feedback

    return score


def main():
    print(f"Model: {MODEL_NAME}")
    print(f"API:   {API_BASE_URL}")
    print(f"Env:   {PING_URL}")
    print("=" * 50)

    scores = {}

    for task in TASKS:
        print(f"\nRunning task: {task}")
        score = run_task(task)
        scores[task] = score

    print("\n" + "=" * 50)
    print("--- Baseline Summary ---")
    for task, score in scores.items():
        print(f"{task:15s} {score:.2f}")


if __name__ == "__main__":
    main()
