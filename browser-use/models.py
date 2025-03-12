from pydantic import BaseModel
from enum import Enum

class TaskOutput(BaseModel):
    task_status: str
    execution_time: str
    completed_at: str
    summary: str
    user_provided_data: dict
    
class BotStates(Enum):
    PROMPT_RECEIVED = 0
    PROCESSING = 1
    TASK_COMPLETE = 2
    
class AgentSpec(BaseModel):
    task: str = None
    llm: str = None
    sensitive_data: dict = None
    key: str = None
    
class Models(Enum):
    GPT_4o = "gpt-4o"
    GPT_4o_mini = "gpt-4o-mini"
