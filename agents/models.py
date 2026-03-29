import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

# --- Agrinet / Suggestions Model (port 8080) ---
AGRINET_MODEL = OpenAIChatModel(
    os.getenv('AGRINET_MODEL_NAME'),
    provider=OpenAIProvider(
        base_url=os.getenv('AGRINET_INFERENCE_URL'),
        api_key=os.getenv('AGRINET_API_KEY', 'no-key'),
    ),
)

# --- Moderation Model (port 8081) ---
MODERATION_MODEL = OpenAIChatModel(
    os.getenv('MODERATION_MODEL_NAME'),
    provider=OpenAIProvider(
    base_url=os.getenv('MODERATION_INFERENCE_URL'),
    api_key=os.getenv('MODERATION_API_KEY', 'no-key'),
),
)