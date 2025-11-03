import os
import re
import httpx
from uuid import uuid4
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI
from models import JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus, Artifact, ExecuteParams, MessageCard, MessagePart


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


app = FastAPI()
client = httpx.AsyncClient()


def extract_pr_url(text: str) -> Optional[str]:
    """
    Find the first GitHub PR link in a message.
    """
    match = re.search(r'(https://github\.com/[\w-]+/[\w-]+/pull/\d+)', text)
    if match:
        return match.group(1)
    return None


async def get_github_pr_diff(pr_url: str) -> str:
    """
    Fetches the .diff file for the given GitHub PR URL.
    """
    diff_url = pr_url + ".diff"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }
    
    try:
        response = await client.get(diff_url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as error:
        print(f"Error fetching diff: {error}")
        return f"Error: Could not fetch diff for {pr_url}. Status code: {error.response.status_code}"
    

async def get_ai_review(diff_text: str) -> str:
    """
    Sends the diff text to the Google Gemini API for review.
    """
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY is not set."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    system_prompt = "You are an expert code reviewer. Review the following code diff. Focus on potential bugs, style issues, or missing error handling. Be concise and provide feedback in 3 bullet points."
    
    json_data = {
        "system_instruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "contents": [
            {
                "parts": [
                    {"text": diff_text}
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = await client.post(api_url, headers=headers, json=json_data, timeout=30.0)
        response.raise_for_status()
        
        data = response.json()
        
        review_text = data['candidates'][0]['content']['parts'][0]['text']
        return review_text
    
    except httpx.HTTPStatusError as error:
        print(f"Error calling Gemini API: {error.response.status_code}")
        print(f"Response body: {error.response.text}")
        return f"Error: The AI review failed with status {error.response.status_code}."
    except Exception as error:
        print(f"An unexpected error calling Gemini: {error}")
        return "Error: The AI review failed."
    
def create_error_response(request_id: str, code: int, error_message: str) -> JSONRPCResponse:
    """
    Creates a JSON-RPC error response.
    """
    return JSONRPCResponse(
        id=request_id,
        error={"code": code, "message": error_message}
        )

    
@app.post("/api/v1/agent/invoke")
async def handle_agent_request(request: JSONRPCRequest) -> JSONRPCResponse:
    """
    Main Enpoint to handle incoming A2A JSON-RPC requests for PR reviews.
    """
    try:
        if request.method != "execute":
            return create_error_response(
                request.id, -32601,
                f"Method not found. This agent only supports 'execute', not '{request.method}'."
            )
        
        # Parse and validate incoming request
        params = ExecuteParams.model_validate(request.params)

        if not params.messages:
            return create_error_response(request.id, -32602, "Invalid params: 'messages' array cannot be empty.")
            
        
        history = params.messages
        last_message = history[-1]
        
        if last_message.role != "user" or not last_message.parts:
            return create_error_response(request.id, -32602, "Invalid params: Last message must be from 'user' and have parts.")
            
        user_text = last_message.parts[0].text
        
        context_id = params.contextId
        task_id = params.taskId or "task-" + str(uuid4())
        
        pr_url = extract_pr_url(user_text)
        if not pr_url:
            raise ValueError("I couldn't find a GitHub PR link in your message.")

        diff_text = await get_github_pr_diff(pr_url)
        if "Error:" in diff_text:
            raise ValueError(diff_text)

        review_text = "This is a fast, hard-coded test reply. If you see this, the AI call is the problem." #await get_ai_review(diff_text)
        if "Error:" in review_text:
            raise ValueError(review_text)

        # Create the JSON-RPC Response
        chat_message = MessageCard(
            role="agent",
            parts=[MessagePart(kind="text", text="Here is the PR review you requested:")]
        )

        artifact = Artifact(
            name="review",
            parts=[MessagePart(kind="text", text=review_text)]
        )
        status = TaskStatus(state="completed", message=chat_message)
        result = TaskResult(
            id=task_id,
            contextId=context_id,
            status=status,
            artifacts=[artifact],
            history=history
        )
        return JSONRPCResponse(id=request.id, result=result)

    except Exception as error:
        # Create JSON-RPC Error Response
        print(f"An unhandled error occurred: {error}")
        return create_error_response(
            request.id, -32000,
            f"An internal server error occurred: {error}"
        )
    

@app.get("/")
def read_root():
    return {"Success": "PR Review Agent is available!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)