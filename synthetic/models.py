import os
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

# Get configurations from environment variables

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()
LLM_AGRINET_MODEL_NAME    = os.getenv('LLM_AGRINET_MODEL_NAME')
LLM_MODERATION_MODEL_NAME = os.getenv('LLM_MODERATION_MODEL_NAME')
ENABLE_INSTRUMENTATION = os.getenv('ENABLE_INSTRUMENTATION', 'false').lower() in ('true', '1', 'yes')
VLLM_AGRINET_MODEL_URL = os.getenv('VLLM_AGRINET_MODEL_URL')
VLLM_MODERATION_MODEL_URL = os.getenv('VLLM_MODERATION_MODEL_URL')


if LLM_PROVIDER == 'vllm':
    LLM_MODEL = OpenAIChatModel(
        LLM_AGRINET_MODEL_NAME,
        provider=OpenAIProvider(
            base_url=VLLM_AGRINET_MODEL_URL,
            api_key="not-required",
        ),
    )
    LLM_MODERATION_MODEL = OpenAIChatModel(
        LLM_MODERATION_MODEL_NAME,
        provider=OpenAIProvider(
            base_url=VLLM_MODERATION_MODEL_URL,
            api_key="not-required",
        ),
    )
elif LLM_PROVIDER == 'openai':
    LLM_AGRINET_MODEL = OpenAIChatModel(
        LLM_AGRINET_MODEL_NAME,
        provider=OpenAIProvider(
            api_key=os.getenv('OPENAI_API_KEY'),
        ),
    )

    LLM_MODERATION_MODEL = OpenAIChatModel(
        LLM_MODERATION_MODEL_NAME,
        provider=OpenAIProvider(
            api_key=os.getenv('OPENAI_API_KEY'),
        ),
    )
elif LLM_PROVIDER == 'azure-openai':
    LLM_AGRINET_MODEL = OpenAIChatModel(
    LLM_AGRINET_MODEL_NAME,
    provider=OpenAIProvider(
        base_url=VLLM_AGRINET_MODEL_URL,
        api_key="not-required",
    ),
    )
    LLM_MODERATION_MODEL = OpenAIChatModel(
        LLM_MODERATION_MODEL_NAME,
        provider=OpenAIProvider(
            base_url=VLLM_MODERATION_MODEL_URL,
            api_key="not-required",
        ),
    )
