import os
import re
import httpx
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI
from models import JSONRPCRequest, JSONRPCResponse, TaskResult, TaskStatus, OutgoingMessage, MessagePart


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
    
@app.post("/api/v1/agent/invoke")
async def handle_agent_request(request: JSONRPCRequest) -> JSONRPCResponse:
    """
    Main Enpoint to handle incoming A2A JSON-RPC requests for PR reviews.
    """
    try:
        # Get the user's message from the request
        user_text = request.params.message.parts[0].text
        
        # Find the PR link in the message
        pr_url = extract_pr_url(user_text)
        
        if not pr_url:
            review_text = "I couldn't find a GitHub PR link in your message. Please paste the full URL."
        else:
            # Get the .diff text from GitHub
            diff_text = await get_github_pr_diff(pr_url)
            
            # Get AI review
            if "Error:" not in diff_text:
                review_text = await get_ai_review(diff_text)
            else:
                review_text = diff_text  # Pass the error message back to user

        # Create successful A2A JSON-RPC response
        response_message = OutgoingMessage(role="agent", parts=[MessagePart(type="text", text=review_text)])
        task_status = TaskStatus(state="completed", message=response_message)
        task_result = TaskResult(status=task_status)
        
        return JSONRPCResponse(result=task_result, id=request.id)

    except Exception as error:
        # Create error response 
        print(f"An unexpected error occurred: {error}")
        error_message = OutgoingMessage(role="agent", parts=[MessagePart(type="text", text=f"An internal error occurred: {error}")])
        task_status = TaskStatus(state="failed", message=error_message)
        task_result = TaskResult(status=task_result)
        return JSONRPCResponse(result=task_result, id=request.id)

@app.get("/")
def read_root():
    return {"Success": "PR Review Agent is available!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)