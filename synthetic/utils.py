"""Utility functions used by the synthetic module (extracted from helpers.utils)."""

import logging
from datetime import datetime
from typing import Dict

from jinja2 import Environment, FileSystemLoader


def get_prompt(prompt_file: str, context: Dict = {}, prompt_dir: str = "assets/prompts") -> str:
    """Load a prompt from a file and format it with a context using Jinja2 templating."""
    if not prompt_file.endswith(".md"):
        prompt_file += ".md"

    env = Environment(
        loader=FileSystemLoader(prompt_dir),
        autoescape=False,
    )
    template = env.get_template(prompt_file)
    return template.render(**context) if context else template.render()


def get_crop_season(dt: datetime) -> str:
    """Classify a date into an Indian agricultural season."""
    month = dt.month
    if 6 <= month <= 9:
        return "Kharif (Monsoon)"
    elif month >= 10 or month <= 2:
        return "Rabi (Winter)"
    else:
        return "Zaid (Summer)"


def get_logger(name: str) -> logging.Logger:
    """Get logger object."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(ch)
    return logger
