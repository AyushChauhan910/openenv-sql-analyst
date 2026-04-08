"""
inference.py — SQL Analyst Agent Environment
"""
import sys
import subprocess

try:
    from openai import OpenAI
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai>=1.0.0", "-q"])
    from openai import OpenAI

import asyncio
import os
import textwrap
import urllib.request
import json
from typing import List, Optional

from openai import OpenAI  # ✅ Checklist item 4

# ✅ Checklist item 1 & 2 — exact pattern required
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")  # no default ✅
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")  # optional

API_KEY = HF_TOKEN or os.getenv("API_KEY")
PING_URL = os.getenv("PING_URL") or "https://ayush0910-openenv-sql-analyst.hf.space"

TASKS = ["easy_sql", "medium_sql", "hard_sql"]
BENCHMARK = "sql-analyst-env"
MAX_STEPS = 10
TEMPERATURE = 0.1
MAX_TOKENS = 500
SUCCESS_SCORE_THRESHOLD = 0.7

SYSTEM_PROMPT = textwrap.dedent("""
    You are a SQL expert. Given a database schema and a business question,
    write a single valid SQL SELECT query to answer it.
    Return ONLY the raw SQL query — no explanations, no markdown, no backticks.
    The query must work on SQLite.
""").strip()


# ── Logging ✅ Checklist item 5 — exact START/STEP/END format ────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").strip()
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── Environment calls (urllib is fine here, only LLM needs OpenAI) ───────────

def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def env_reset(task_name: str) -> dict:
    return http_post(f"{PING_URL}/reset", {"task_name": task_name})


def env_step(sql_query: str) -> dict:
    return http_post(f"{PING_URL}/step", {"sql_query": sql_query})


# ── LLM call via OpenAI client ✅ ─────────────────────────────────────────────

def get_sql_from_model(client: OpenAI, obs: dict, step: int, history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    last_result = obs.get("last_query_result") or "None"

    user_prompt = textwrap.dedent(f"""
        Step: {step}
        Schema:
        {obs.get("schema_info", "")}

        Question: {obs.get("question", "")}

        Last query result: {last_result}

        Previous steps:
        {history_block}

        Write the SQL query to answer the question.
    """).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.lower().startswith("sql"):
                text = text[3:]
        return text.strip() if text else "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "SELECT 1"


# ── Task runner ───────────────────────────────────────────────────────────────

async def run_task(client: OpenAI, task_name: str) -> float:
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env_reset(task_name)

        for step in range(1, MAX_STEPS + 1):
            if obs.get("done"):
                break

            sql = get_sql_from_model(client, obs, step, history)

            try:
                result = env_step(sql)
            except Exception as e:
                print(f"[DEBUG] env_step failed: {e}", flush=True)
                log_step(step=step, action=sql, reward=0.0, done=False, error=str(e))
                break

            reward = float(result.get("reward", 0.0))
            done = result.get("done", False)
            error = result.get("info", {}).get("feedback") if reward == 0.0 else None
            obs = result.get("observation", obs)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=sql, reward=reward, done=done, error=error)
            history.append(f"Step {step}: reward={reward:.2f}")

            if done:
                break

        score = max(rewards) if rewards else 0.0
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task {task_name} error: {e}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)  # ✅ OpenAI client

    results = {}
    for task in TASKS:
        print(f"\n--- Running {task} ---", flush=True)
        score = await run_task(client, task)
        results[task] = score

    print(f"\n{'='*50}", flush=True)
    print("BASELINE SUMMARY", flush=True)
    for task, score in results.items():
        print(f"{task:<15} {score:.3f}", flush=True)
    print(f"{'='*50}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())