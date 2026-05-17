import os
import sys
from dotenv import load_dotenv
load_dotenv('.env')

from langchain_openai import ChatOpenAI
import logging
import httpx

logging.basicConfig(level=logging.DEBUG)

print("Starting LLM call...")
llm = ChatOpenAI(
    model=os.environ["AI_MODEL_NAME"],
    api_key=os.environ["AI_API_KEY"],
    base_url=os.environ["AI_API_BASE_URL"],
    timeout=5,
)

try:
    res = llm.invoke("hello")
    print(res)
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")

