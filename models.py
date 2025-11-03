from pydantic import BaseModel, Field
from typing import Any, List, Literal, Optional
from datetime import datetime
from uuid import uuid4


# --- Incoming Request Model
class MessagePart(BaseModel):
  type: Literal["text", "file"]
  text: Optional[str] = None


class MessageCard:
  kind: Literal["message"] = "message"
  role: Literal["user", "agent", "system"]
  parts: List[MessagePart]
  messageId: str = Field(default_factory=lambda: str(uuid4()))
  taskId: Optional[str] = None

class PushNotificationConfig(BaseModel):
  url: str
  token: Optional[str] = None
  authentication: Optional[Dict[str, Any]] = None

class MessageConfig(BaseModel):
  blocking: bool = True
  acceptedOutputModes: List[str] = ["text/plain"]
  pushNotificationConfig: Optional[PushNotificationConfig] = None

class TaskParams(BaseModel):
  message: MessageCard
  configuration: MessageConfig = Field(default_factory=MessageConfiguration)

class RequestContext(BaseModel):
  contextId: Optional[str] = None
  taskId: Optional[str] = None
  messages: List[MessageCard]

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: Literal["message/send", "execute"]
    params: TaskParams | RequestContext

class TaskStatus(BaseModel):
  state: Literal["working", "completed", "input-required", "failed"]
  timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
  message: Optional[MessageCard] = None

class Artifact(BaseModel):
  artifactId: str = Field(default_factory=lambda: str(uuid4()))
  name: str
  parts: List[MessagePart]

class TaskResult(BaseModel):
  id: str
  contextId: str
  status: TaskStatus
  artifacts: List[Artifact] = []
  history: List[MessageCard] = []
  kind: Literal["task"] = "task"

class JSONRPCResponse(BaseModel):
  jsonrpc: Literal["2.0"] = "2.0"
  id: str
  result: Optional[TaskResult] = None
  error: Optional[Dict[str, Any]] = None 
