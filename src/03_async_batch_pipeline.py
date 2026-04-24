import os
import asyncio
import instructor
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
# TODO: Import tenacity for retry logic (e.g., retry, stop_after_attempt, wait_exponential)

load_dotenv()

# Async client patched with Instructor for batch processing
client = instructor.from_openai(
    AsyncOpenAI(
        api_key=os.getenv("API_KEY"), 
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    ),
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
    # async with semaphore:
    
    # Note: We use create_with_completion to get BOTH the parsed object AND the raw API response (for token usage)
    parsed_obj, raw_response = await client.chat.completions.create_with_completion(
        model="gemini-3-flash-preview",
        response_model=CloudIncident,
        messages=[{"role": "user", "content": log_text}]
    )
    
    # TODO: Extract token usage from the 'raw_response' object to track costs
    # hint: raw_response.usage.prompt_tokens and raw_response.usage.completion_tokens
    
    return parsed_obj

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
    # Pricing for Gemini Flash: Assume $0.075 per 1M input tokens, $0.30 per 1M output tokens.

if __name__ == "__main__":
    asyncio.run(main())