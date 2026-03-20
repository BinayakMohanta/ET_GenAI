# Domain-Specialized AI Agents with Compliance Guardrails 

Minimal instructions to run the Healthcare Compliance Agent API and frontend.

## Prerequisites
- Python 3.10+ installed
- (Optional) Ollama running locally with model `qwen2.5:7b` if you want LLM responses

## Setup (Windows PowerShell)
1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. (Optional) Ensure Ollama is running and the model `qwen2.5:7b` is available.

## Run

Start the API (FastAPI / uvicorn):

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Serve the frontend `index.html` (simple static server):

```powershell
# from project root
python -m http.server 5500
```

Open the frontend at: http://localhost:5500/index.html
API base: http://127.0.0.1:8000

## Test the `/chat` endpoint (PowerShell example)

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/chat -ContentType "application/json" -Body (@{message="Headache"; role="Medical_Professional"; session_id="test1"} | ConvertTo-Json)
```

## Notes
- If Ollama is not available or the named model is missing, the API will error when invoking the LLM.
- `.gitignore` excludes `.venv/` and editor artifacts.
