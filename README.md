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
Modern LLMs are smart enough to output valid JSON syntax if you ask nicely (or use `response_format={"type": "json_object"}`). However, in Data Engineering, valid JSON is not enough. We need **Strict Type Enforcement**. 

Look at `src/01_naive_extraction.py`. This script attempts to extract multiple cloud incidents from a messy log. Crucially, the log contains an edge case: Ticket 103 has an "unknown" downtime.

**Your Task:** 
1. Run the script: `python src/01_naive_extraction.py`
2. **Notice the pipeline crash:** The LLM returns valid JSON, but it struggles with the `downtime_minutes` constraint for Ticket 103. It either returns `null` or a string like `"unknown"`. When Python attempts to multiply this by 60 to calculate seconds for the database, the script throws a `TypeError` and dies. 
3. **The Lesson:** Prompt engineering is not a reliable ETL strategy. 

---
## Part 2: Deterministic Structured Outputs (Pydantic & Instructor)
We must treat the LLM as a function that returns a strongly-typed, validated object. Look at `src/02_structured_extraction.py`. We use `Pydantic` to define our exact SQL schema in Python, and the `Instructor` library to patch the LLM client.

**Your Task:**
1. Run the script: `python src/02_structured_extraction.py`
2. Observe how the edge case is handled flawlessly. By defining `downtime_minutes` as `Optional[int]`, Pydantic forces the LLM to either provide a valid integer or `None`. If the LLM makes a mistake, `Instructor` catches the error locally and *automatically reprompts the LLM* to fix its own JSON before your Python code ever sees it.
3. **Experiment:** Modify the `Incident` Pydantic class. Add a new field: `is_security_breach: bool = Field(description="True if the cause was malicious")`. Re-run the script and observe how the LLM automatically adapts to the new schema constraints.

---
## Part 3: The Engineering Challenge (Async Scaling & FinOps)
Processing 1 document takes 1 second. Processing 1,000 documents sequentially takes 16 minutes. As Data Engineers, we use `asyncio` to process them concurrently. However, hitting an LLM API concurrently will instantly result in a **429 Too Many Requests (Rate Limit)** error.

Open `src/03_async_batch_pipeline.py`. 

**Your Engineering Tasks:**
1. **Concurrency Control:** The current script tries to fire all 100 requests at once and will crash. Implement an `asyncio.Semaphore` to limit concurrent API calls to 5.
2. **Resilience:** Wrap the LLM call in a retry block using the `tenacity` library (implement `wait_exponential`) so if the API hits a 429 error, it waits and retries instead of crashing the entire ETL job.
3. **FinOps (Cost Tracking):** Cloud API endpoints return token usage metadata in the response. Modify the code to accumulate the `prompt_tokens` and `completion_tokens`. At the end of the script, calculate and print the total cost of this ETL job (Assume $0.075 per 1M input tokens, and $0.30 per 1M output tokens for the Flash model).