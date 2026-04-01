import random as rng
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from server.models import Observation, Reward
from server.database.schema import get_db_connection, get_schema_info
from server.tasks.easy import EasyTask
from server.tasks.medium import MediumTask
from server.tasks.hard import HardTask
from server.graders.sql_grader import SQLGrader

app = FastAPI(title="OpenEnv SQL Analyst", version="1.0.0")

TASK_REGISTRY = {
    "easy_sql": EasyTask,
    "medium_sql": MediumTask,
    "hard_sql": HardTask,
}

current_task = None
current_connection = None
step_count: int = 0
episode_history: list[dict] = []
schema_info: str = ""
episode_done: bool = False

grader = SQLGrader()


class ResetRequest(BaseModel):
    task_name: Optional[str] = None


class StepRequest(BaseModel):
    sql_query: str


@app.get("/")
async def root():
    return {"message": "SQL Analyst Agent Environment", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/reset")
async def reset(request: ResetRequest):
    global current_task, current_connection, step_count, episode_history, schema_info, episode_done

    task_name = request.task_name
    if task_name is None:
        task_name = rng.choice(list(TASK_REGISTRY.keys()))

    if task_name not in TASK_REGISTRY:
        return {"error": f"Unknown task: {task_name}. Choose from: {list(TASK_REGISTRY.keys())}"}

    current_task = TASK_REGISTRY[task_name]()
    current_connection, schema_info = get_db_connection()
    step_count = 0
    episode_history = []
    episode_done = False

    observation = Observation(
        schema_info=schema_info,
        question=current_task.get_question(),
        db_state="initialized",
        last_query_result=None,
        last_reward=0.0,
        step=0,
        done=False
    )

    return observation.model_dump()


@app.post("/step")
async def step(request: StepRequest):
    global current_task, current_connection, step_count, episode_history, episode_done

    if current_task is None or current_connection is None:
        return {"error": "No active episode. Call /reset first."}

    step_count += 1

    expected = current_task.get_expected()
    reward = grader.grade(
        sql_query=request.sql_query,
        expected=expected,
        connection=current_connection
    )

    done = reward.score >= 1.0 or step_count >= current_task.get_max_steps()
    episode_done = done

    last_query_result = _format_query_result(request.sql_query, current_connection)

    episode_history.append({
        "step": step_count,
        "sql_query": request.sql_query,
        "score": reward.score,
        "feedback": reward.feedback
    })

    observation = Observation(
        schema_info=schema_info,
        question=current_task.get_question(),
        db_state="query_executed",
        last_query_result=last_query_result,
        last_reward=reward.score,
        step=step_count,
        done=done
    )

    return {
        "observation": observation.model_dump(),
        "reward": reward.score,
        "done": done,
        "info": {
            "feedback": reward.feedback,
            "partial_credit": reward.partial_credit
        }
    }


@app.get("/state")
async def state():
    if current_task is None:
        return {"error": "No active episode. Call /reset first."}

    observation = Observation(
        schema_info=schema_info,
        question=current_task.get_question(),
        db_state="query_executed" if step_count > 0 else "initialized",
        last_query_result=episode_history[-1]["sql_query"] if episode_history else None,
        last_reward=episode_history[-1]["score"] if episode_history else 0.0,
        step=step_count,
        done=episode_done
    )

    return observation.model_dump()


def _format_query_result(sql_query: str, connection) -> Optional[str]:
    try:
        cursor = connection.execute(sql_query)
        rows = cursor.fetchall()
        if not rows:
            return "No rows returned"

        columns = [desc[0] for desc in cursor.description]
        lines = [" | ".join(columns), "-" * (len(columns) * 15)]

        for row in rows[:10]:
            lines.append(" | ".join(str(v) for v in row))

        if len(rows) > 10:
            lines.append(f"... ({len(rows) - 10} more rows)")

        return "\n".join(lines)
    except Exception:
        return None


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
