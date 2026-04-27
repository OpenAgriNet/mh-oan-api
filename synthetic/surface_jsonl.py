"""JSONL text = what the user saw (Bhili after NMT, etc.).

Agents still run with English inside for ``bhb``; we only fix copies for disk.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from pydantic_ai.messages import ModelMessagesTypeAdapter, ModelMessage, ModelRequest, ModelResponse


def _last_assistant_text(msgs: list[ModelMessage], text: str) -> None:
    for i in range(len(msgs) - 1, -1, -1):
        m = msgs[i]
        if not isinstance(m, ModelResponse):
            continue
        for j in range(len(m.parts) - 1, -1, -1):
            if getattr(m.parts[j], "part_kind", None) == "text":
                m.parts[j] = replace(m.parts[j], content=text)
                return


def _first_user_prompt(msgs: list[ModelMessage], content: str) -> None:
    for m in msgs:
        if not isinstance(m, ModelRequest):
            continue
        for j, p in enumerate(m.parts):
            if getattr(p, "part_kind", None) == "user-prompt":
                m.parts[j] = replace(p, content=content)
                return


def add_farmer_turn(buf: list[ModelMessage], user_run) -> None:
    chunk = deepcopy(user_run.new_messages())
    out = user_run.output
    _last_assistant_text(chunk, out if isinstance(out, str) else str(out))
    buf.extend(chunk)


def add_agrinet_turn(
    buf: list[ModelMessage],
    full_history: list[ModelMessage],
    prefix_len: int,
    user_prompt_shown: str,
    reply_shown: str,
) -> None:
    chunk = deepcopy(full_history[prefix_len:])
    _first_user_prompt(chunk, user_prompt_shown)
    _last_assistant_text(chunk, reply_shown)
    buf.extend(chunk)


def to_json(buf: list[ModelMessage]) -> str:
    return ModelMessagesTypeAdapter.dump_json(buf).decode()
