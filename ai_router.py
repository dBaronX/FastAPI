#  ai_router.py

import os
import time
from typing import Tuple
from pydantic import BaseModel
from fastapi import HTTPException
from openai import OpenAI, APIError
import anthropic
import google.generativeai as genai
import requests  # for any extra

class StoryResponse(BaseModel):
    story: str
    provider: str
    model: str
    estimated_cost_usd: float = 0.0

# Initialize clients once (at module level)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_story(prompt: str, max_retries: int = 2) -> StoryResponse:
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")

    providers = [
        ("gemini", lambda: gemini_generate(prompt)),
        ("openai", lambda: openai_generate(prompt)),
        ("anthropic", lambda: anthropic_generate(prompt)),
    ]

    for provider_name, generator in providers:
        for attempt in range(max_retries + 1):
            try:
                story_text, model = generator()
                # Rough cost estimate (update with real token pricing later)
                cost = 0.0005 if provider_name == "gemini" else 0.002 if provider_name == "openai" else 0.003
                return StoryResponse(
                    story=story_text,
                    provider=provider_name,
                    model=model,
                    estimated_cost_usd=cost
                )
            except Exception as e:
                print(f"❌ {provider_name} attempt {attempt+1} failed: {e}")
                if attempt == max_retries:
                    continue  # try next provider
                time.sleep(1)  # simple backoff

    # All failed
    raise HTTPException(status_code=503, detail="All AI providers failed. Try again later.")

# Helper functions
def gemini_generate(prompt: str) -> Tuple[str, str]:
    model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-pro"
    res = model.generate_content(prompt)
    return res.text, "gemini-1.5-flash"

def openai_generate(prompt: str) -> Tuple[str, str]:
    res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return res.choices[0].message.content, "gpt-4o-mini"

def anthropic_generate(prompt: str) -> Tuple[str, str]:
    res = anthropic_client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return res.content[0].text, "claude-3-haiku"