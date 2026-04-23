import os
import asyncio
import instructor
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
# TODO: Import tenacity for retry logic

load_dotenv()

# Async client for batch processing
client = instructor.from_openai(
    AsyncOpenAI(api_key=os.getenv("API_KEY"), base_url="https://api.groq.com/openai/v1"),
    mode=instructor.Mode.JSON
)

class CloudIncident(BaseModel):
    incident_id: str
    downtime_minutes: int

# Mocking 100 log files to process
logs_to_process = [f"Ticket #10{i}: Server crashed in eu-west-1. Down for {10+i} minutes." for i in range(100)]

# TODO: Add Tenacity @retry decorator here to handle rate limits (429 errors)
async def process_log(log_text: str, semaphore: asyncio.Semaphore):
    # TODO: Implement the semaphore context manager here to throttle concurrency
    
    response, completion = await client.chat.completions.create_with_completion(
        model="llama3-8b-8192",
        response_model=CloudIncident,
        messages=[{"role": "user", "content": log_text}]
    )
    
    # TODO: Extract token usage from the 'completion' object to track costs
    # hint: completion.usage.prompt_tokens
    
    return response

async def main():
    print(f"Starting async ETL pipeline for {len(logs_to_process)} documents...")
    
    # TODO: Initialize asyncio.Semaphore (Start with 5 concurrent requests)
    semaphore = None 
    
    tasks = [process_log(log, semaphore) for log in logs_to_process]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if isinstance(r, CloudIncident))
    print(f"Successfully processed {success_count}/{len(logs_to_process)} records.")
    
    # TODO: Print the total cost of the ETL job based on token usage

if __name__ == "__main__":
    asyncio.run(main())