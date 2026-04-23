# Lab 1: GenAI for ETL & Unstructured Data Extraction

## Objective
Data Engineers spend 80% of their time cleaning and structuring chaotic data. Generative AI can automate this, but naive LLM usage fails in production because LLMs hallucinate fields or wrap JSON in Markdown format (which breaks SQL databases). 

In this lab, you will:
1. Observe the failure of standard prompt engineering for ETL.
2. Force an LLM to output a strict, deterministic database schema using `Pydantic` and `Instructor`.
3. Build a high-throughput, asynchronous batch-processing pipeline that respects cloud API rate limits and tracks token costs.

## Setup
1. Clone this repository.
2. Create a virtual environment: `python -m venv venv` and activate it:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file in the root directory. Add your API key (You can use a free Google Gemini API key or Groq API key):
   ```env
   API_KEY=your_api_key_here
   ```

---

## Part 1: The Naive Approach (Execution & Observation)
Look at `src/01_naive_extraction.py`. This script attempts to extract cloud incident data from a raw text log using standard prompt engineering.

**Your Task:** 
1. Run the script: `python src/01_naive_extraction.py`
2. Look at the output. Try to parse it directly into a Python dictionary using `json.loads()`. 
3. **Notice the failure:** The LLM likely wrapped the output in ` ```json ` markdown blocks, or missed the exact data types (e.g., returning `"45 minutes"` instead of the integer `45`). This will crash a data pipeline.

---

## Part 2: Deterministic Structured Outputs
We must treat the LLM as a function that returns a strongly-typed object. Look at `src/02_structured_extraction.py`. We use `Pydantic` to define our SQL schema and `Instructor` to patch the LLM client to force Tool Calling/JSON mode.

**Your Task:**
1. Run the script: `python src/02_structured_extraction.py`
2. Observe how the output is no longer a string, but a validated Python object (Pydantic model) ready for a database `INSERT`.
3. **Experiment:** Modify the `CloudIncident` Pydantic class. Add a new field: `is_security_breach: bool`. Re-run the script and observe how the LLM automatically adapts to the new schema constraints.

---

## Part 3: The Engineering Challenge (Async Scaling & FinOps)
Processing 1 document takes 1 second. Processing 1,000 documents sequentially takes 16 minutes. As Data Engineers, we use `asyncio` to process them concurrently. However, hitting an LLM API concurrently will result in a **429 Too Many Requests (Rate Limit)** error.

Open `src/03_async_batch_pipeline.py`. 

**Your Engineering Tasks:**
1. **Concurrency Control:** The current script tries to fire all 100 requests at once and will crash. Implement an `asyncio.Semaphore` to limit concurrent API calls to 5.
2. **Resilience:** Wrap the LLM call in a retry block using the `tenacity` library (implement Exponential Backoff) so if it hits a 429 error, it waits and retries instead of crashing the ETL job.
3. **FinOps (Cost Tracking):** The API returns token usage in the response. Modify the code to accumulate the `prompt_tokens` and `completion_tokens`. At the end of the script, calculate and print the total cost of this ETL job (Assume $0.15 per 1M input tokens, and $0.60 per 1M output tokens).
```