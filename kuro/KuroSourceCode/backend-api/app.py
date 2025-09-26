from fastapi import FastAPI, Request
from typing import List, Dict, Any
from google import genai
from google.genai import types
from prompts import ORIGINAL_PROMPT
from fastapi.responses import PlainTextResponse

app = FastAPI()
client = genai.Client(api_key="yourkey")

def aiResponse(prompt: str, answer: str, history: List[Dict[str, str]]):
    contents = []

    # Optional: system instructions or original prompt
    contents.append(types.Content(role="user", parts=[types.Part(text=ORIGINAL_PROMPT)]))

    for message in history:
        # Add user message if exists
        if message.get("user"):
            contents.append(types.Content(role="user", parts=[types.Part(text=message["user"])]))
        # Add model message if it exists
        if message.get("model"):
            contents.append(types.Content(role="model", parts=[types.Part(text=message["model"])]))

    # Now add the latest user answer
    contents.append(types.Content(role="user", parts=[types.Part(text=answer)]))

    # Let Gemini respond to that
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=500,
        ),
        contents=contents,
    )

    return response.text


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Backend is connected and running!"}

@app.post("/", response_class=PlainTextResponse)
async def chat(payload: Dict[str, Any]):
    prompt = payload.get("prompt", "")
    history = payload.get("history", [])

    response_text = aiResponse(prompt, history)
    return response_text
