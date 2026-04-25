from pydantic_ai import Agent, RunContext
from synthetic.utils import get_prompt
from synthetic.models import LLM_AGRINET_MODEL, ENABLE_INSTRUMENTATION
from synthetic.tools import TOOLS
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from synthetic.deps import FarmerContext

_AGRINET_MODEL_SETTINGS = OpenAIResponsesModelSettings(
    # temperature=0.7,
    # top_p=0.95,
    parallel_tool_calls=True,
    timeout=120,
    openai_text_verbosity="medium",
    # max_tokens=4096,
    openai_reasoning_effort="medium",
)

agrinet_agent = Agent(
    model=LLM_AGRINET_MODEL,
    name="Vistaar Agent",
    instrument=ENABLE_INSTRUMENTATION,
    output_type=str,
    deps_type=FarmerContext,
    retries=3,
    tools=TOOLS,
    end_strategy='exhaustive',
    model_settings=_AGRINET_MODEL_SETTINGS,
)


@agrinet_agent.system_prompt(dynamic=True)
def get_system_prompt(ctx: RunContext[FarmerContext]):
    deps = ctx.deps
    lang_code = deps.lang_code or 'en'

    # Map Bhili to English for prompt selection
    prompt_lang = 'en' if lang_code == 'bhb' else lang_code
    
    prompt_name = f'agrinet_system_{prompt_lang}'
    return get_prompt(prompt_name, context={
        'today_date': deps.get_today_date_str(),
        'crop_season': deps.crop_season,
    })
