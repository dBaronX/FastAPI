import os
from openai import OpenAI
import anthropic
import google.generativeai as genai

# INIT
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_story(prompt: str):

    # 1️⃣ GEMINI (CHEAPEST FIRST)
    try:
        model = genai.GenerativeModel("gemini-pro")
        res = model.generate_content(prompt)
        return res.text, "gemini"
    except Exception as e:
        print("❌ Gemini failed:", e)

    # 2️⃣ OPENAI
    try:
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content, "openai"
    except Exception as e:
        print("❌ OpenAI failed:", e)

    # 3️⃣ ANTHROPIC
    try:
        res = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text, "anthropic"
    except Exception as e:
        print("❌ Anthropic failed:", e)

    return "All AI providers failed.", "none"