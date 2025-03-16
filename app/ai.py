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
                "content": "You are a professional hazard report analyst. Your task is to concisely summarize events and provide actionable suggestions where necessary."
            },
            {
                "role": "user",
                "content": f"Based on the following event information, write one or two summarizing the situation and provide 1-3 specific suggestions for addressing it if necessary:\n\n{event}"
            }
        ]
    )
    return completion.choices[0].message.content
