import os
import logfire
from dotenv import load_dotenv

load_dotenv()

logfire.configure(scrubbing=False, environment=os.getenv("ENVIRONMENT"))
