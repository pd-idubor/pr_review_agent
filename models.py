from pydantic import BaseModel, Field
from typing import List, Literal, Tuple
from uuid import uuid4


# Request Model
class MessagePart(BaseModel):
    kind: Literal["text"]
    text: str

class DataPart(BaseModel):
    kind: Literal["data"]
    data: List[MessagePart]

class IncomingMessage(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["user", "agent", "system"]
    parts: Tuple[MessagePart, DataPart]
    messageId: str


class TaskParams(BaseModel):
    message: IncomingMessage
  
class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: Literal["message/send", "execute"]
    params: TaskParams

# Response Model
class OutgoingMessage(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["agent"]
    parts: List[MessagePart]

class TaskStatus(BaseModel):
    state: Literal["completed", "failed"]
    message: OutgoingMessage

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
