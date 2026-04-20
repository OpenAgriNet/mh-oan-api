from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

# langfuse = Langfuse()
Agent.instrument_all()