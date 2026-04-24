import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
) 

# ADVERSARIAL LOG: Contains multiple incidents. Ticket 103 has NO known integer for downtime.
raw_log = """
Incident Report:
- Ticket 101: us-east-1 went down for 45 mins. Cause: Redis leak.
- Ticket 102: eu-west-1 had latency spikes. Downtime: None, just slow.
- Ticket 103: ap-south-1 offline. Downtime duration is currently unknown, team is still investigating.
"""

prompt = f"""
Extract the incidents from the log into a JSON array named "incidents". 
Each object must have these exact keys:
- incident_id (string)
- primary_region (string)
- downtime_minutes (integer)
- root_cause (string)

Log: {raw_log}
"""

print("Fetching from LLM...\n")
try:
    response = client.chat.completions.create(
        model="gemini-3-flash-preview", 
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"} 
    )

    raw_output = response.choices[0].message.content
    print("RAW LLM OUTPUT:")
    print(raw_output)
    print("-" * 40)

    # --- THE DATA ENGINEERING TEST ---
    parsed_data = json.loads(raw_output)
    
    print("\nAttempting to process data for Database Insertion...")
    
    for incident in parsed_data["incidents"]:
        region = incident["primary_region"]
        
        # The Crash Point: What does the LLM do with Ticket 103's "unknown" downtime?
        # If it returned null, NoneType * 60 = Crash
        # If it returned "unknown", String * 60 = Crash (or logical failure in Python)
        downtime_seconds = incident["downtime_minutes"] * 60 
        
        print(f"SUCCESS: {region} was down for {downtime_seconds} seconds.")

except KeyError as e:
    print(f"\n[PIPELINE CRASH] Missing Expected Key: {e}")
except TypeError as e:
    print(f"\n[PIPELINE CRASH] Data Type Error: {e}")
    print("Lesson: The LLM could not enforce the 'integer' constraint on missing data!")
except Exception as e:
    print(f"\n[PIPELINE CRASH] Error: {e}")