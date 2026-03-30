from pydantic_ai import Agent, RunContext
from helpers.utils import get_prompt, get_today_date_str, get_crop_season
from agents.models import AGRINET_MODEL
from agents.tools import TOOLS
from pydantic_ai.settings import ModelSettings
from agents.deps import FarmerContext


# Qwen3.5 27B — no-thinking mode recommended settings
# vLLM server should be started with: --reasoning-parser qwen3
_AGRINET_MODEL_SETTINGS = ModelSettings(
    temperature=0.7,
    top_p=0.8,
    max_tokens=32768,
    parallel_tool_calls=True,
    request_limit=50,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": False},
        "top_k": 20,
        "presence_penalty": 1.5,
    },
)

agrinet_agent = Agent(
    model=AGRINET_MODEL,
    name="Vistaar Agent",
    instrument=True,
    output_type=str,
    deps_type=FarmerContext,
    retries=3,
    tools=TOOLS,
    end_strategy='exhaustive',
    model_settings=_AGRINET_MODEL_SETTINGS,
)

@agrinet_agent.system_prompt(dynamic=True)
def get_agrinet_system_prompt(ctx: RunContext[FarmerContext]):
    lang_code = ctx.deps.lang_code or 'en'
    prompt_name = f'agrinet_system_{lang_code}'
    return get_prompt(prompt_name, context={
        'today_date': get_today_date_str(),
        'crop_season': get_crop_season(),
    })