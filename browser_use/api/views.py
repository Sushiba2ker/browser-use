
from pydantic import BaseModel, Field
from typing import Optional, Any

class TaskRequest(BaseModel):
    task: str
    model_name: Optional[str] = 'gpt-4o'

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    
    class Config:
        arbitrary_types_allowed = True

class TaskCreateResponse(BaseModel):
    task_id: str
    status: str 