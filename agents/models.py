from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI
import httpx
import os
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.settings import ModelSettings
from dotenv import load_dotenv
from helpers.utils import get_logger

logger = get_logger(__name__)
load_dotenv()

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'vllm').lower()
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')

_VLLM_FULL_EXTRA_BODY = {
    "presence_penalty": 1.5,
    "chat_template_kwargs": {"enable_thinking": False},
    "top_k": 20,
}

_AZURE_FALLBACK_SETTINGS = ModelSettings(extra_body=None)


def _vllm_settings(base_url):
    if LLM_PROVIDER != "vllm" or not base_url:
        return None
    if "openai.com" in base_url.lower() or "azure.com" in base_url.lower():
        return ModelSettings(extra_body={"presence_penalty": _VLLM_FULL_EXTRA_BODY["presence_penalty"]})
    return ModelSettings(extra_body=_VLLM_FULL_EXTRA_BODY)


def _make_azure_model():
    return OpenAIChatModel(
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        provider=AzureProvider(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        ),
        settings=_AZURE_FALLBACK_SETTINGS,
    )


def _make_vllm_model(model_name, base_url, http_client):
    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(openai_client=AsyncOpenAI(
            base_url=base_url,
            api_key="not-required",
            http_client=http_client,
            max_retries=0,
        )),
        settings=_vllm_settings(base_url),
    )


if LLM_PROVIDER == 'vllm':
    logger.info("LLM_PROVIDER=%s using vLLM with Azure fallback", LLM_PROVIDER)

    azure_model = _make_azure_model()
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=2.0))

    AGRINET_MODEL = FallbackModel(
        _make_vllm_model(os.environ["LLM_AGRINET_MODEL_NAME"], os.environ["VLLM_AGRINET_MODEL_URL"], http_client),
        azure_model,
    )
    MODERATION_MODEL = FallbackModel(
        _make_vllm_model(os.environ["LLM_MODERATION_MODEL_NAME"], os.environ["VLLM_MODERATION_MODEL_URL"], http_client),
        azure_model,
    )

elif LLM_PROVIDER == 'azure-openai':
    logger.info("LLM_PROVIDER=%s using Azure OpenAI", LLM_PROVIDER)
    AGRINET_MODEL = _make_azure_model()
    MODERATION_MODEL = AGRINET_MODEL

else:
    raise ValueError(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Must be one of: 'vllm', 'azure-openai'")