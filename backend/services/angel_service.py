from openai import AsyncOpenAI
import os
from utils.constant import ANGEL_SYSTEM_PROMPT

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TAG_PROMPT = "Reminder: Before asking the next question, include a machine-readable tag in this format:\n[[Q:<PHASE>.<NN>]] — e.g. [[Q:BUSINESS_PLAN.03]] What is your pricing model?"

async def get_angel_reply(user_msg, history):
    # Always default to "hi" if input is empty
    if not user_msg.get("content") or user_msg["content"].strip() == "":
        user_msg["content"] = "hi"

    msgs = [
        {"role": "system", "content": ANGEL_SYSTEM_PROMPT},
        {"role": "system", "content": TAG_PROMPT},
        *history,
        {"role": "user", "content": user_msg["content"].strip()}
    ]

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=msgs,
        temperature=0.7
    )

    return response.choices[0].message.content
