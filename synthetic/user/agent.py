"""
Synthetic farmer user agent — an LLM that role-plays as a Maharashtra farmer
to drive multi-turn conversations with the agrinet agent.
"""

from typing import Union

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModelSettings

from synthetic.utils import get_prompt
from synthetic.mock_data import scheme_display_name
from synthetic.models import LLM_USER_MODEL
from synthetic.user.profile import FarmerProfile
from synthetic.user.tools import EndConversation

user_agent = Agent[FarmerProfile, Union[str, EndConversation]](
    model=LLM_USER_MODEL,
    name="Farmer User",
    instrument=True,
    output_type=Union[str, EndConversation],  # type: ignore[arg-type]
    deps_type=FarmerProfile,
    retries=3,
    end_strategy='exhaustive',
    model_settings=OpenAIChatModelSettings(
        #openai_reasoning_effort="low",
        # temperature=0.7,
        # top_p=0.8,
        # presence_penalty=1.5,
        # extra_body={
        #     "top_k": 20,
        #     "chat_template_kwargs": {"enable_thinking": False},
        # },
    ),
)


@user_agent.system_prompt
async def system_prompt(ctx):
    profile = ctx.deps
    return get_prompt("user_agent", context={
        "name": profile.name,
        "village": profile.village,
        "taluka": profile.taluka,
        "district": profile.district,
        "state": profile.state,
        "phone": profile.phone,
        "farmer_id": profile.farmer_id,
        "crops": ", ".join(profile.crops),
        "land_acres": profile.land_acres,
        "mood": profile.mood,
        "verbosity": profile.verbosity,
        "language": profile.language,
        "use_latin_script": profile.use_latin_script,
        "scenario_description": profile.scenario["description"],
        "mahadbt_scheme_codes": ", ".join(scheme_display_name(c) for c in profile.mahadbt_scheme_codes) if profile.mahadbt_scheme_codes else "None",
    })
