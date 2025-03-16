from openai import OpenAI
from .config import get_settings

settings = get_settings()
client = OpenAI(api_key=settings.openai_api_key)

def generate_event_description(event: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a hazard report analyst tool. Your task is to concisely summarize events and provide actionable suggestions where necessary."
            },
            {
                "role": "user",
                "content": f"Based on the following event information, write one or two summarizing the situation. do not use any special symbols and do not state tat it is a summary. export only the raw text. keep it short:\n\n{event}"
            }
        ],
        max_tokens=30
    )
    return completion.choices[0].message.content
