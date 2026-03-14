from pydantic_ai import Agent
from synthetic.utils import get_prompt
from synthetic.models import LLM_AGRINET_MODEL
from pydantic_ai.models.openai import OpenAIResponsesModelSettings
from synthetic.deps import FarmerContext



TRANSLATOR_MODEL_SETTINGS = OpenAIResponsesModelSettings(
    parallel_tool_calls=True,
    timeout=120,
    openai_text_verbosity="medium",
    openai_reasoning_effort="high",
)

translator_agent = Agent(
    model=LLM_AGRINET_MODEL,
    name="Translator Agent",
    instrument=True,
    output_type=str,
    deps_type=FarmerContext,
    retries=3,
    end_strategy='exhaustive',
    model_settings=TRANSLATOR_MODEL_SETTINGS,
)


@translator_agent.system_prompt()
def get_system_prompt():
    prompt_name = f'translation_bhb'
    return get_prompt(prompt_name)


async def improve_bhb_translation(en_text: str, bhb_text: str) -> str:
    """
    Improve the Bhili translation of the given English text.
    """
    user_prompt = f"""## Task: Correct this machine-translated Bhili text

### English Source (reference for meaning and formatting):
{en_text}

---

### Machine-Translated Bhili Draft (correct this):
{bhb_text}

---

### Correction Instructions:
1. **Read the English source** to understand the exact meaning, structure, and formatting.
2. **Identify errors in the draft** — look for:
   - Marathi grammar leaking in (चा/ची/चे instead of ना/नी/नू, आहे instead of शे, -ावे/-ायला instead of -नं)
   - Lazy transliterations of farming terms (use खत not फर्टिलायझर, नत्र not नायट्रोजन, etc.)
   - Unnatural sentence structure that doesn't sound like spoken Nandurbar Bhili
   - Any Roman alphabet characters
3. **Output ONLY the corrected Bhili translation** — match the English source formatting exactly (bold, bullets, line breaks)."""

    result = await translator_agent.run(user_prompt)
    return result.output
