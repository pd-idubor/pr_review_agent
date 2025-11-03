import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from .models import JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus, Artifact, MessageCard, MessagePart


load_dotenv()
app = FastAPI()
cl



if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)