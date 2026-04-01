from typing import Tuple, Dict, Any
from server.models import Observation, Action, Reward
from server.tasks.easy import EASY_TASKS
from server.tasks.medium import MEDIUM_TASKS
from server.tasks.hard import HARD_TASKS
from server.graders.sql_grader import SQLGrader
from server.database.schema import get_schema_info


class SQLEnvironment:
    def __init__(self):
        self.tasks = {**EASY_TASKS, **MEDIUM_TASKS, **HARD_TASKS}
        self.grader = SQLGrader()
        self.current_task = None
        self.current_step = 0
        self.max_steps = 5

    def reset(self, task_name: str = None) -> Observation:
        if task_name is None:
            import random
            task_name = random.choice(list(self.tasks.keys()))

        self.current_task = self.tasks[task_name]
        self.current_step = 0

        return Observation(
            schema_info=get_schema_info(),
            question=self.current_task["question"],
            db_state="initialized",
            last_query_result=None,
            last_reward=0.0,
            step=0,
            done=False
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        if self.current_task is None:
            raise ValueError("Environment not reset. Call reset() first.")

        self.current_step += 1
        reward = self.grader.grade(
            sql_query=action.sql_query,
            expected_sql=self.current_task["expected_sql"],
            task_config=self.current_task
        )

        done = reward.score >= 1.0 or self.current_step >= self.max_steps

        observation = Observation(
            schema_info=get_schema_info(),
            question=self.current_task["question"],
            db_state="query_executed",
            last_query_result=str(reward.feedback),
            last_reward=reward.score,
            step=self.current_step,
            done=done
        )

        info = {
            "task_name": self.current_task.get("name", "unknown"),
            "steps_taken": self.current_step
        }

        return observation, reward, done, info
