import os
import instructor
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Patch the client with Instructor to enforce Pydantic schemas
client = instructor.from_openai(
    OpenAI(api_key=os.getenv("API_KEY"), base_url="https://api.groq.com/openai/v1"),
    mode=instructor.Mode.JSON
)

# Define the exact database schema using Pydantic
class CloudIncident(BaseModel):
    incident_id: str = Field(description="The ticket number or incident ID")
    region: str = Field(description="The cloud region affected")
    downtime_minutes: int = Field(description="Total downtime calculated in minutes")
    root_cause: str = Field(description="Brief summary of the root cause")

raw_log = """
Ticket #9942: At 03:00 AM UTC, the payment gateway cluster in us-east-1 went down. 
Customers couldn't check out. We found a memory leak in the redis cache. 
Rebooted the nodes and restored service at 03:45 AM UTC.
"""

# The LLM will now return a validated CloudIncident object, not a string.
incident: CloudIncident = client.chat.completions.create(
    model="llama3-8b-8192",
    response_model=CloudIncident,
    messages=[{"role": "user", "content": raw_log}]
)

print(f"Validated Python Object: {type(incident)}")
print(f"Incident ID: {incident.incident_id}")
print(f"Downtime: {incident.downtime_minutes} mins")
print(f"Ready for SQL Insert: {incident.model_dump_json()}")