import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI, AsyncOpenAI

load_dotenv()

# --- Agrinet / Suggestions Model (port 8080) ---
AGRINET_MODEL = OpenAIModel(
    os.getenv('AGRINET_MODEL_NAME'),
    provider=OpenAIProvider(
        base_url=os.getenv('AGRINET_INFERENCE_URL'),
        api_key=os.getenv('AGRINET_API_KEY', 'no-key'),
    ),
)

# --- Moderation Model (port 8081) ---
MODERATION_CLIENT = AsyncOpenAI(
    base_url=os.getenv('MODERATION_INFERENCE_URL'),
    api_key=os.getenv('MODERATION_API_KEY', 'no-key'),
)