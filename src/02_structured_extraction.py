# 1. Silence the annoying Mac SSL warning
import warnings
warnings.filterwarnings("ignore", module="urllib3")

import os
import instructor
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Patch the OpenAI client with Instructor. 
# Changed to Mode.TOOLS (the industry standard for Function Calling)
client = instructor.from_openai(
    OpenAI(
        api_key=os.getenv("API_KEY"), 
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    ),
    mode=instructor.Mode.TOOLS
)

# Define the exact database schema using Pydantic
class Incident(BaseModel):
    incident_id: str = Field(description="The ticket number or incident ID")
    primary_region: str = Field(description="The cloud region affected")
    downtime_minutes: Optional[int] = Field(description="Total downtime in minutes. If unknown, return null.", default=None)
    root_cause: str = Field(description="Brief summary of the root cause")

# Bypassing the Python 3.9 nested evaluation bug by using standard types
class IncidentReport(BaseModel):
    incidents: List[Incident] = Field(default_factory=list)

# The exact same adversarial log from Part 1
raw_log = """
Incident Report:
- Ticket 101: us-east-1 went down for 45 mins. Cause: Redis leak, spoofing.
- Ticket 102: eu-west-1 had latency spikes. Downtime: None, just slow.
- Ticket 103: ap-south-1 offline. Downtime duration is currently unknown, team is still investigating.
"""

print("Fetching and validating via Instructor...\n")

try:
    # The LLM will now return a validated Python object
    report = client.chat.completions.create(
        model="gemini-3-flash-preview",
        response_model=IncidentReport,
        messages=[{"role": "user", "content": f"Extract the incidents: {raw_log}"}]
    )

    print(f"Validated Python Object: {type(report)}")
    print("-" * 40)

    for inc in report.incidents:
        print(f"ID: {inc.incident_id} | Region: {inc.primary_region} | Downtime: {inc.downtime_minutes} | Cause: {inc.root_cause} ")

    print("\nSUCCESS: Notice how Ticket 103's downtime safely defaulted to 'None' instead of crashing!")

except Exception as e:
    print(f"\n[ERROR] The script failed: {e}")