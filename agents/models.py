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
FALLBACK_LLM_PROVIDER = os.getenv('FALLBACK_LLM_PROVIDER', 'azure-openai').lower()
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

VLLM_ENABLE_UNSAFE_EXTRA_BODY = os.getenv("VLLM_ENABLE_UNSAFE_EXTRA_BODY", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# vLLM extra body:
# - Some keys (e.g. `top_k`, `chat_template_kwargs`) are rejected by OpenAI/Azure.
# - We keep `extra_body` OpenAI-safe by default, and only enable vLLM-only keys
#   with an explicit env opt-in.
VLLM_EXTRA_BODY = (
    (
        {"presence_penalty": 1.5}
        | (
            {
                "chat_template_kwargs": {"enable_thinking": False},
                "top_k": 20,
            }
            if VLLM_ENABLE_UNSAFE_EXTRA_BODY
            else {}
        )
    )
    if LLM_PROVIDER == "vllm"
    else None
)

def _vllm_settings_for_base_url(base_url: str | None) -> ModelSettings | None:
    """
    Only attach vLLM-only parameters when we are actually talking to vLLM.

    Misconfiguration happens frequently (e.g. pointing a "vLLM_*_MODEL_URL" at OpenAI/Azure).
    OpenAI/Azure reject vLLM-only keys like `chat_template_kwargs` and `top_k`.
    """
    if LLM_PROVIDER != "vllm" or not VLLM_EXTRA_BODY:
        return None
    if not base_url:
        return None

    # Even if the URL doesn't obviously look like OpenAI/Azure (custom domains, proxies),
    # keep the payload compatible unless the operator explicitly opted in to vLLM-only keys.
    if not VLLM_ENABLE_UNSAFE_EXTRA_BODY:
        return ModelSettings(extra_body=VLLM_EXTRA_BODY)

    lowered = base_url.lower()
    if "openai.com" in lowered or "azure.com" in lowered:
        return ModelSettings(extra_body={"presence_penalty": VLLM_EXTRA_BODY.get("presence_penalty", 0.0)})

    return ModelSettings(extra_body=VLLM_EXTRA_BODY)

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

    if not LLM_AGRINET_MODEL_NAME:
        raise ValueError('LLM_AGRINET_MODEL_NAME environment variable is required when LLM_PROVIDER=vllm')
    if not LLM_MODERATION_MODEL_NAME:
        raise ValueError('LLM_MODERATION_MODEL_NAME environment variable is required when LLM_PROVIDER=vllm')
    if not VLLM_AGRINET_MODEL_URL:
        raise ValueError('VLLM_AGRINET_MODEL_URL environment variable is required when LLM_PROVIDER=vllm')
    if not VLLM_MODERATION_MODEL_URL:
        raise ValueError('VLLM_MODERATION_MODEL_URL environment variable is required when LLM_PROVIDER=vllm')

    azure_model = _make_azure_model()

    AGRINET_MODEL = FallbackModel(
        OpenAIChatModel(
            LLM_AGRINET_MODEL_NAME,
            provider=OpenAIProvider(
                base_url=VLLM_AGRINET_MODEL_URL,
                api_key="not-required",
            ),
            settings=_vllm_settings_for_base_url(VLLM_AGRINET_MODEL_URL),
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
            settings=_vllm_settings_for_base_url(VLLM_MODERATION_MODEL_URL),
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