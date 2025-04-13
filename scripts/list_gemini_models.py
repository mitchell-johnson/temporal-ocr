import os
import google.generativeai as genai
import asyncio

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=api_key)

async def list_models():
    models = genai.list_models()
    print("Available models:")
    for model in models:
        print(f"- Name: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Supported generation methods: {model.supported_generation_methods}")
        print()

if __name__ == "__main__":
    asyncio.run(list_models()) 