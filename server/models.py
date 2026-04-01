from typing import Optional
from pydantic import BaseModel


class Observation(BaseModel):
    schema_info: str
    question: str
    db_state: str
    last_query_result: Optional[str] = None
    last_reward: float = 0.0
    step: int = 0
    done: bool = False


class Action(BaseModel):
    sql_query: str


class Reward(BaseModel):
    score: float
    feedback: str
    partial_credit: dict = {}
