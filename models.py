from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
from datetime import datetime


class MessagePart(BaseModel):
    kind: Literal["text", "data", "file"]
    text: Optional[str] = None
    data: Optional[Any] = None
    file_url: Optional[str] = None

class MessageCard(BaseModel):
    kind: Literal["message"] = "message"
    role: Literal["user", "agent", "system"]
    parts: List[MessagePart]
    messageId: str = Field(default_factory=lambda: str(uuid4()))
    taskId: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PushNotificationConfig(BaseModel):
    url: str
    token: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None

class MessageConfig(BaseModel):
    blocking: bool = True
    acceptedOutputModes: List[str] = ["text/plain", "image/png"]
    historyLength: Optional[int] = None
    pushNotificationConfig: Optional[PushNotificationConfig] = None

class TaskParams(BaseModel):
    message: MessageCard
    configuration: MessageConfig = Field(default_factory=lambda: MessageConfig)

class ExecuteParams(BaseModel):
    contextId: Optional[str] = None
    taskId: Optional[str] = None
    messages: List[MessageCard]

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: Literal["message/send", "execute"]
    params: TaskParams | ExecuteParams

class TaskStatus(BaseModel):
    state: Literal["working", "completed", "input-required" "failed"]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    message: Optional[MessageCard] = None

class Artifact(BaseModel):
    artifactId: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    parts: List[MessagePart]

class TaskResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    contextId: str = Field(default_factory=lambda: str(uuid4()))
    status: TaskStatus
    artifacts: List[Artifact] = []
    history: List[MessageCard] = []
    kind: Literal["task"] = "task"

class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: str
    result: Optional[TaskResult] = None
    error: Optional[Dict[str, Any]] = None
