from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncOpenAI, APIError
import httpx
import os
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.exceptions import ModelAPIError, ConcurrencyLimitExceeded, UnexpectedModelBehavior
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.concurrency import ConcurrencyLimitedModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.openai import OpenAIChatModelSettings
from pydantic_ai.concurrency import ConcurrencyLimiter
from dotenv import load_dotenv
from helpers.utils import get_logger

logger = get_logger(__name__)
load_dotenv()

AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')

agrinet_vllm_settings = ModelSettings(
    temperature=0.7,
    top_p=0.95,
    presence_penalty=1.5,
    extra_body={
        "top_k": 20,
        "min_p": 0.0,
        "repetition_penalty": 1.0,
        "chat_template_kwargs": {"enable_thinking": False},
    },
)

moderation_vllm_settings = OpenAIChatModelSettings(
    temperature=1.0,
    top_p=1.0,
    openai_reasoning_effort='low',
)

azure_settings = ModelSettings(extra_body=None)

http_client = httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=2.0))
agrinet_limiter = ConcurrencyLimiter(max_running=10, max_queued=0, name='agrinet-vllm')
moderation_limiter = ConcurrencyLimiter(max_running=10, max_queued=0, name='moderation-vllm')


def _make_vllm_model(model_name, base_url, settings):
    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(openai_client=AsyncOpenAI(
            base_url=base_url,
            api_key="not-required",
            http_client=http_client,
            max_retries=0,
        )),
        settings=settings,
    )


def _make_azure_model():
    return OpenAIChatModel(
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        provider=AzureProvider(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=AZURE_OPENAI_API_VERSION,
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        ),
        settings=azure_settings,
    )


azure_model = _make_azure_model()

AGRINET_MODEL = FallbackModel(
    ConcurrencyLimitedModel(
        _make_vllm_model(os.environ["LLM_AGRINET_MODEL_NAME"], os.environ["VLLM_AGRINET_MODEL_URL"], agrinet_vllm_settings),
        limiter=agrinet_limiter,
    ),
    azure_model,
    fallback_on=(ModelAPIError, APIError, ConcurrencyLimitExceeded, UnexpectedModelBehavior),
)

MODERATION_MODEL = FallbackModel(
    ConcurrencyLimitedModel(
        _make_vllm_model(os.environ["LLM_MODERATION_MODEL_NAME"], os.environ["VLLM_MODERATION_MODEL_URL"], moderation_vllm_settings),
        limiter=moderation_limiter,
    ),
    azure_model,
    fallback_on=(ModelAPIError, APIError, ConcurrencyLimitExceeded, UnexpectedModelBehavior),
)
