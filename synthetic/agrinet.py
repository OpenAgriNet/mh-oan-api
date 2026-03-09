from pydantic_ai import Agent, RunContext
from helpers.utils import get_prompt
from synthetic.models import LLM_AGRINET_MODEL, ENABLE_INSTRUMENTATION
from synthetic.tools import TOOLS
from pydantic_ai.models.openai import OpenAIChatModelSettings
from synthetic.deps import FarmerContext

_AGRINET_MODEL_SETTINGS = OpenAIChatModelSettings(
    # temperature=0.7,
    # top_p=0.95,
    timeout=120,
    max_tokens=4096,
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
    return get_prompt('agrinet_system', context={
        'today_date': deps.get_today_date_str(),
    })
