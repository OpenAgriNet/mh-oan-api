import os
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.settings import ModelSettings
from dotenv import load_dotenv
from helpers.utils import get_logger

logger = get_logger(__name__)
load_dotenv()

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'vllm').lower()

# vLLM config
LLM_AGRINET_MODEL_NAME = os.getenv('LLM_AGRINET_MODEL_NAME')
LLM_MODERATION_MODEL_NAME = os.getenv('LLM_MODERATION_MODEL_NAME')
VLLM_AGRINET_MODEL_URL = os.getenv('VLLM_AGRINET_MODEL_URL')
VLLM_MODERATION_MODEL_URL = os.getenv('VLLM_MODERATION_MODEL_URL')

# Azure config
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

# vLLM-specific extra body — only valid for vLLM, never sent to Azure
VLLM_EXTRA_BODY = {
    "chat_template_kwargs": {"enable_thinking": False},
    "top_k": 20,
    "presence_penalty": 1.5,
} if LLM_PROVIDER == "vllm" else None

# Azure model settings explicitly clears extra_body
_AZURE_FALLBACK_SETTINGS = ModelSettings(extra_body=None)


def _make_azure_model() -> OpenAIChatModel:
    if not AZURE_OPENAI_ENDPOINT:
        raise ValueError('AZURE_OPENAI_ENDPOINT environment variable is required')
    if not AZURE_OPENAI_API_KEY:
        raise ValueError('AZURE_OPENAI_API_KEY environment variable is required')
    if not AZURE_OPENAI_DEPLOYMENT_NAME:
        raise ValueError('AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required')
    return OpenAIChatModel(
        AZURE_OPENAI_DEPLOYMENT_NAME,
        provider=AzureProvider(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=AZURE_OPENAI_API_KEY,
        ),
        # Ensures vLLM extra_body params are never forwarded to Azure
        settings=_AZURE_FALLBACK_SETTINGS,
    )


if LLM_PROVIDER == 'vllm':
    logger.info("LLM_PROVIDER=%s using vLLM with Azure fallback", LLM_PROVIDER)

    azure_model = _make_azure_model()

    AGRINET_MODEL = FallbackModel(
        OpenAIChatModel(
            LLM_AGRINET_MODEL_NAME,
            provider=OpenAIProvider(
                base_url=VLLM_AGRINET_MODEL_URL,
                api_key="not-required",
            ),
        ),
        azure_model,
    )
    MODERATION_MODEL = FallbackModel(
        OpenAIChatModel(
            LLM_MODERATION_MODEL_NAME,
            provider=OpenAIProvider(
                base_url=VLLM_MODERATION_MODEL_URL,
                api_key="not-required",
            ),
        ),
        azure_model,
    )

elif LLM_PROVIDER == 'azure-openai':
    logger.info("LLM_PROVIDER=%s using Azure OpenAI", LLM_PROVIDER)
    azure_model = _make_azure_model()
    AGRINET_MODEL = azure_model
    MODERATION_MODEL = azure_model

else:
    raise ValueError(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Must be one of: 'vllm', 'azure-openai'")