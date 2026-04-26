"""
Synthetic conversation generation pipeline for MH-OAN.

Orchestrates multi-turn conversations between a synthetic Maharashtra farmer user
agent and the agrinet agent, with environment randomization, parallel batch
generation, and JSONL output.

Usage:
    python -m synthetic.generate -n 10 --max-parallel 5 --max-turns 10 --output-dir data/synthetic
"""

import argparse
import asyncio
import json
import random
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from synthetic.agrinet import agrinet_agent
from synthetic.deps import FarmerContext, build_moderation_input
from synthetic.mock_data import TARGET_LANGUAGE_WEIGHTS, SAME_LANGUAGE_PROBABILITY, LANGUAGE_SWITCH_PROBABILITY
from synthetic.models import LLM_AGRINET_MODEL_NAME
from synthetic.moderation import moderation_agent
from synthetic.translation import BhashiniTranslator
from synthetic.user import (
    EndConversation,
    FarmerProfile,
    generate_random_profile,
    user_agent,
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ConversationEnv(BaseModel):
    """Randomized environment configuration for a single conversation."""
    today_date: datetime
    target_language: str
    session_id: str
    user_model: str
    user_model_settings: dict
    agrinet_model: str
    agrinet_model_settings: dict


class LanguageSwitch(BaseModel):
    """Records a mid-conversation target language switch."""
    turn: int
    from_lang: str
    to_lang: str


class ConversationRecord(BaseModel):
    """Output record for a single completed conversation."""
    session_id: str
    env: ConversationEnv
    profile: FarmerProfile
    agrinet_messages_json: str
    user_messages_json: str
    turn_count: int
    completed: bool
    error: str | None = None
    language_switches: list[LanguageSwitch] | None = None


# ---------------------------------------------------------------------------
# Environment generation
# ---------------------------------------------------------------------------


def generate_random_environment(target_language: str | None = None) -> ConversationEnv:
    """Build a randomized ConversationEnv."""
    if target_language is None:
        langs, weights = zip(*TARGET_LANGUAGE_WEIGHTS.items())
        target_language = random.choices(langs, weights=weights, k=1)[0]

    return ConversationEnv(
        today_date=datetime.now() + timedelta(days=random.randint(0, 365)),
        target_language=target_language,
        session_id=str(uuid4()),
        user_model=LLM_AGRINET_MODEL_NAME,
        user_model_settings=dict(user_agent.model_settings)
        if user_agent.model_settings
        else {},
        agrinet_model=LLM_AGRINET_MODEL_NAME,
        agrinet_model_settings=dict(agrinet_agent.model_settings)
        if agrinet_agent.model_settings
        else {},
    )


# ---------------------------------------------------------------------------
# Conversation runner
# ---------------------------------------------------------------------------


def _pick_language_switch(current_lang: str, max_turns: int) -> tuple[int, str] | None:
    """Decide whether this conversation has a language switch."""
    if random.random() >= LANGUAGE_SWITCH_PROBABILITY:
        return None
    switch_turn = random.randint(2, max(2, max_turns - 1))
    candidates = {k: v for k, v in TARGET_LANGUAGE_WEIGHTS.items() if k != current_lang}
    langs, weights = zip(*candidates.items())
    new_lang = random.choices(langs, weights=weights, k=1)[0]
    return switch_turn, new_lang


async def run_conversation(
    env: ConversationEnv,
    profile: FarmerProfile,
    max_turns: int = 25,
) -> ConversationRecord:
    """Run a multi-turn conversation between the user and agrinet agents."""

    current_target_lang = env.target_language
    language_switches: list[LanguageSwitch] = []

    # Initialize Bhili translators (only used if current_target_lang is 'bhb')
    bhili_to_en_translator = BhashiniTranslator(source_lang='bhb', target_lang='en')
    en_to_bhili_translator = BhashiniTranslator(source_lang='en', target_lang='bhb')

    planned_switch = _pick_language_switch(current_target_lang, max_turns)

    farmer_ctx = FarmerContext(
        query="",
        lang_code=current_target_lang,
        session_id=env.session_id,
        today_date=env.today_date,
        farmer_id=profile.farmer_id if profile.has_agristack else None,
        farmer_name=profile.name,
        farmer_phone=profile.phone,
        farmer_state=profile.state,
        farmer_district=profile.district,
        farmer_taluka=profile.taluka,
        farmer_village=profile.village,
        farmer_village_code=profile.village_code,
        farmer_crops=profile.crops,
        farmer_land_acres=profile.land_acres,
        farmer_gender=profile.gender,
        farmer_caste_category=profile.caste_category,
        farmer_latitude=profile.latitude,
        farmer_longitude=profile.longitude,
        farmer_is_pocra=profile.is_pocra,
    )

    # First turn — user agent speaks first
    user_result = await user_agent.run(
        "Begin the conversation based on your goal.",
        deps=profile,
    )

    if current_target_lang == "bhb":
        user_result.output = await en_to_bhili_translator.translate_text(
            user_result.output, source_lang="en", target_lang="bhb"
        )

    agrinet_history = []
    user_history = user_result.all_messages()
    turn_count = 0
    completed = False

    for _ in range(max_turns):
        turn_count += 1

        # Check for language switch
        if planned_switch and turn_count == planned_switch[0]:
            old_lang = current_target_lang
            current_target_lang = planned_switch[1]
            language_switches.append(LanguageSwitch(
                turn=turn_count, from_lang=old_lang, to_lang=current_target_lang,
            ))

        user_output = user_result.output
        if isinstance(user_output, EndConversation):
            completed = True
            break

        user_text = user_output
        if current_target_lang == 'bhb':
            user_text_for_processing = await bhili_to_en_translator.translate_text(
                user_text, source_lang='bhb', target_lang='en'
            )
        else:
            user_text_for_processing = user_text

        mod_input = build_moderation_input(user_text_for_processing, agrinet_history, limit=3)
        mod_result = await moderation_agent.run(mod_input)

        agrinet_lang_code = 'en' if current_target_lang == 'bhb' else current_target_lang

        farmer_ctx = FarmerContext(
            query=user_text_for_processing,
            lang_code=agrinet_lang_code,
            session_id=env.session_id,
            today_date=env.today_date,
            moderation_str=str(mod_result.output),
            farmer_id=profile.farmer_id if profile.has_agristack else None,
            farmer_name=profile.name,
            farmer_phone=profile.phone,
            farmer_state=profile.state,
            farmer_district=profile.district,
            farmer_taluka=profile.taluka,
            farmer_village=profile.village,
            farmer_village_code=profile.village_code,
            farmer_crops=profile.crops,
            farmer_land_acres=profile.land_acres,
            farmer_gender=profile.gender,
            farmer_caste_category=profile.caste_category,
            farmer_latitude=profile.latitude,
            farmer_longitude=profile.longitude,
            farmer_is_pocra=profile.is_pocra,
        )

        # Run agrinet agent
        agrinet_result = await agrinet_agent.run(
            user_prompt=farmer_ctx.get_user_message(),
            deps=farmer_ctx,
            message_history=agrinet_history,
        )
        agrinet_history = agrinet_result.all_messages()

        if current_target_lang == "bhb":
            agrinet_response_for_user = await en_to_bhili_translator.translate_text(
                agrinet_result.output, source_lang="en", target_lang="bhb"
            )
        else:
            agrinet_response_for_user = agrinet_result.output

        # Run user agent with agrinet's response
        user_result = await user_agent.run(
            user_prompt=agrinet_response_for_user,
            deps=profile,
            message_history=user_history,
        )

        if current_target_lang == "bhb":
            user_result.output = await en_to_bhili_translator.translate_text(
                user_result.output, source_lang="en", target_lang="bhb"
            )

        user_history = user_result.all_messages()

    return ConversationRecord(
        session_id=env.session_id,
        env=env,
        profile=profile,
        agrinet_messages_json=agrinet_result.all_messages_json()
        if turn_count > 0
        else "[]",
        user_messages_json=user_result.all_messages_json(),
        turn_count=turn_count,
        completed=completed,
        language_switches=language_switches or None,
    )


# ---------------------------------------------------------------------------
# Batch generation
# ---------------------------------------------------------------------------


async def generate_batch(
    n: int,
    max_parallel: int = 5,
    output_dir: str = "data/synthetic",
    max_turns: int = 25,
    mood: str | None = None,
    scenario_ids: list[str] | None = None,
) -> Path:
    """Generate a batch of n synthetic conversations and write to JSONL."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(max_parallel)

    async def _run_one(index: int) -> None:
        async with semaphore:
            env = generate_random_environment()
            user_lang = env.target_language if random.random() < SAME_LANGUAGE_PROBABILITY else None
            sid = scenario_ids[index % len(scenario_ids)] if scenario_ids else None
            profile = generate_random_profile(language=user_lang, mood=mood, scenario_id=sid)
            scenario_id = profile.scenario.get("id", "unknown")

            try:
                record = await run_conversation(env, profile, max_turns=max_turns)
            except Exception:
                record = ConversationRecord(
                    session_id=env.session_id,
                    env=env,
                    profile=profile,
                    agrinet_messages_json="[]",
                    user_messages_json="[]",
                    turn_count=0,
                    completed=False,
                    error=traceback.format_exc(),
                )

            conv_file = output_path / f"{env.session_id}.jsonl"
            with open(conv_file, "w") as f:
                f.write(record.model_dump_json() + "\n")

            print(
                f"[{index + 1}/{n}] session={record.session_id} "
                f"scenario={scenario_id} turns={record.turn_count} "
                f"completed={record.completed}"
                + (f" ERROR" if record.error else "")
            )

    tasks = [asyncio.create_task(_run_one(i)) for i in range(n)]
    await asyncio.gather(*tasks)

    print(f"\nWrote {n} conversations to {output_path}/")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic farmer-agent conversations for MH-OAN.",
    )
    parser.add_argument("-n", type=int, default=25, help="Number of conversations (default: 25)")
    parser.add_argument("--max-parallel", type=int, default=5, help="Max concurrent conversations (default: 5)")
    parser.add_argument("--max-turns", type=int, default=25, help="Max turns per conversation (default: 25)")
    parser.add_argument("--output-dir", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--mood", type=str, default=None, choices=["normal", "frustrated", "adversarial"], help="Force a specific mood")
    parser.add_argument("--scenario", type=str, nargs="+", default=None, help="Force specific scenario ID(s), cycles through them")
    args = parser.parse_args()

    asyncio.run(
        generate_batch(
            n=args.n,
            max_parallel=args.max_parallel,
            output_dir=args.output_dir,
            max_turns=args.max_turns,
            mood=args.mood,
            scenario_ids=args.scenario,
        )
    )


if __name__ == "__main__":
    main()
