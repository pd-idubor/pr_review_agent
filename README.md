# 🤖 Telex.im PR Review Agent

An AI agent built with Python and FastAPI, designed to integrate with the `Telex.im` A2A (Agent-to-Agent) protocol.

The agent listens for messages containing a GitHub Pull Request URL. When it receives one, it fetches the `.diff` file from the GitHub API, sends the code changes to the Google Gemini API for analysis, and then posts a concise, AI-generated code review back to the chat.

## :sparkles: Features

* **Automated Code Reviews:** Get an AI "review on any PR.
* **AI Analysis:** Uses Google Gemini to analyze code diffs for potential bugs, style issues, and missing error handling.
* **`Telex.im` Integration:** Receives and responds using the A2A JSON-RPC protocol.
* **Modern Python Stack:** Built with FastAPI, Pydantic (for data validation), and HTTX (for asynchronous API calls).

## 🛠️ Tech Stack

* **Backend:** Python 3.10+
* **Framework:** FastAPI
* **Dependency Management:** Poetry
* **Production Server:** Gunicorn + Uvicorn
* **Core APIs:**
    * Google Gemini API
    * GitHub API

## Getting Started (Local Development)

Follow these steps to run the agent on your local machine for testing.

### 1. Clone the Repository

```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git)
cd YOUR_REPOSITORY
```

### 2. Install Dependencies
This project uses Poetry for dependency management
```bash
poetry install
```

### 3. Set Up Environment Variables
Create a `.env` file in the root of the project.
```Ini, TOML
# .env
# Your API key from Google AI Studio
GEMINI_API_KEY=your-gemini-key

# Your Personal Access Token from Github
GITHUB_TOKEN=your_github_pat-token
```

### 4. Run the Development Server
Start the server using uvicorn, with auto-reload enabled for easy development
```bash
poetry run uvicorn main:app --reload
```
The server will be running at ```http://127.0.0.1:8000```.

## :rocket: Deployment (Railway)
1. Push to GitHub
2. **Create a Railway Project**
* Create a new project and link to your GitHub repository
3. **Add Variables**
* Go to the "Variables" tab for your new service.
* Add your GEMINI_API_KEY and GITHUB_TOKEN here.
4. **Set the start command**
* Go to the "Settings" tab.
* In the "Deploy" section, set the Start Command to:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --host 0.0.0.0 --port $PORT
```
Railway will automatically deploy your application. Use the public URL it provides (e.g., my-bot.up.railway.app) in your Telex.im workflow JSON.

## Testing the Agent
The agent exposes a single endpoint that follows the A2A protocol.
* **Endpoint:** `post /api/v1/agent/invoke`
* **Method:** `POST`
Test this endpoint using `curl` or an API client

**Sample Request(`curl`)
```bash
curl -X POST "[http://127.0.0.1:8000/api/v1/agent/invoke](http://127.0.0.1:8000/api/v1/agent/invoke)" \
-H "Content-Type: application/json" \
-d '{
    "jsonrpc": "2.0",
    "id": "test-request-123",
    "method": "execute",
    "params": {
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": "Hey, can you review this? [https://github.com/fastapi/fastapi/pull/11200](https://github.com/fastapi/fastapi/pull/11200)"
                }
            ]
        }
    }
}'
```

**Sample Success Response**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "id": "a1b2c3d4-...",
    "status": {
      "state": "completed",
      "message": {
        "role": "agent",
        "parts": [
          {
            "type": "text",
            "text": "Here's my review of the PR:\n\n* **Refactor:** The change simplifies the `Header` dependency logic by moving it into a dedicated `get_header_config` function, which improves modularity.\n* **Style:** The code looks clean and follows the project's existing style.\n* **Suggestion:** No potential issues found; this looks like a solid refactor."
          }
        ]
      }
    },
    "final": true
  },
  "id": "test-request-123"
}
```