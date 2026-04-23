import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# Using an OpenAI compatible endpoint (e.g., Groq, Gemini, or standard OpenAI)
client = OpenAI(api_key=os.getenv("API_KEY"), base_url="https://api.groq.com/openai/v1") 

raw_log = """
Ticket #9942: At 03:00 AM UTC, the payment gateway cluster in us-east-1 went down. 
Customers couldn't check out. We found a memory leak in the redis cache. 
Rebooted the nodes and restored service at 03:45 AM UTC.
"""

prompt = f"""
Extract the following information from the log into JSON format:
- incident_id (string)
- region (string)
- downtime_minutes (integer)
- root_cause (string)

Log: {raw_log}
"""

response = client.chat.completions.create(
    model="llama3-8b-8192", # Adjust model name based on your provider
    messages=[{"role": "user", "content": prompt}]
)

print("RAW LLM OUTPUT:\n")
print(response.choices.message.content)
# Try doing json.loads(response.choices.message.content) here. It will likely fail.