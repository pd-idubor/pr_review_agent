from pydantic import BaseModel, Field
from typing import List, Literal
from uuid import uuid4


# Request Model
class MessagePart(BaseModel):
    type: Literal["text"]
    text: str


class MessageCard(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["user", "agent", "system"]
    parts: List[MessagePart]

class TaskParams(BaseModel):
    message: MessageCard
  
class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: str
    params: TaskParams

# Response Model
class TaskStatus(BaseModel):
    state: Literal["completed", "failed"]
    message: MessageCard

class TaskResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: TaskStatus
    kind: Literal["task"] = "task"
    final: bool = True

class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str
    result: TaskResult
    # error: Optional[Dict[str, Any]] = None 
