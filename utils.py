import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_markdown(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("```", "")
    text = text.replace("---", "")
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.lstrip("# ")
        if line.startswith("#"):
            cleaned.append(stripped)
        else:
            cleaned.append(line)
    return "\n".join(cleaned)


def ai_request(system_msg: str, user_msg: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=3000,
    )
    return clean_markdown(response.choices[0].message.content)


async def send_long_message(message, text: str) -> None:
    if len(text) > 4000:
        parts = [text[i : i + 4000] for i in range(0, len(text), 4000)]
        for part in parts:
            await message.reply_text(part)
    else:
        await message.reply_text(text)
