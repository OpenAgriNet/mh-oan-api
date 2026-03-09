"""
Tools available to the synthetic farmer user agent.
"""

from pydantic import BaseModel


class EndConversation(BaseModel):
    """Returned by the user agent when the conversation is complete."""
