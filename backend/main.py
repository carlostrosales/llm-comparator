import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI, APIStatusError
from anthropic import AsyncAnthropic
from fastapi import FastAPI, HTTPException
from typing import List, Literal
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

load_dotenv(override=True)

app = FastAPI()

app.mount("/assets", StaticFiles(directory=os.path.join(os.getenv("STATIC_DIR", "static"), "assets")), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# -------------------------------------------------------- Pydantic Schemas --------------------------------------------------------

class RunRequest(BaseModel):
    seed_prompt: str | None = None
    competitors: List[str] = [
        "gpt-4o-mini",
        "claude-3-7-sonnet-latest",
        "gemini-2.0-flash",
        "deepseek-chat",
        "llama-3.3-70b-versatile",
    ]

class RankedResult(BaseModel):
    question: str
    answers: List[dict]
    ranking: List[str]
    raw_ranking_json: str

# -------------------------------------------------------- Core Helpers --------------------------------------------------------

async def generate_question(client: AsyncOpenAI, seed_prompt: str) -> str:
    """
    Ask the model to generate a challenging, nuanced question. 
    Returns the question text.
    """
    try:
        resp = await client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": seed_prompt}], timeout=30)
        return resp.choices[0].message.content.strip()
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI API error ({e.status.code}): {e.message}") from e


async def query_gpt(client: AsyncOpenAI, question: str, model_name: str) -> str:
    try:
        resp = await client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": question}])
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}") from e


async def query_claude(client: AsyncAnthropic, question: str, model_name: str) -> str:
    try:
        resp = await client.messages.create(model=model_name, messages=[{"role": "user", "content": question}], max_tokens=1000)
        return resp.content[0].text.strip()
    except Exception as e:
        raise RuntimeError(f"Claude API error: {str(e)}") from e


async def format_responses(answers: list) -> any:
    together = ""
    for index, answer in enumerate(answers):
        together += f"# Response from competitor {index + 1}\n\n"
        together += answer + "\n\n"
    return together

async def rank_responses(client: AsyncOpenAI, competitors: list, question, together) -> str:

    try:
        judge = f"""You are judging a competition between {len(competitors)} competitors.

        {question}

        Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
        Respond with JSON, and only JSON, with the following format:
        {{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

        Here are the responses from each competitor:

        {together}

        Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

        judge_messages = [{"role": "user", "content": judge}]

        # judgment time
        response = await client.chat.completions.create(
            model="o3-mini",
            messages=judge_messages,
        )
        return response.choices[0].message.content.strip()
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI API error ({e.status.code}): {e.message}") from e


async def print_rankings(rankings, competitors) -> None:
    # Turn into readable results
    results_dict = json.loads(rankings)
    ranks = results_dict["results"]
    for index, result in enumerate(ranks):
        competitor = competitors[int(result) - 1]
        print(f"Rank {index+1}: {competitor}")




# -------------------------------------------------------- Main Endpoint --------------------------------------------------------

@app.get("/")
async def serve_react_index():
    return FileResponse(os.path.join(os.getenv("STATIC_DIR", "static"), "index.html"))


@app.post("/run", response_model=RankedResult)
async def run_competition(body: RunRequest):
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')

    if not openai_api_key or not anthropic_api_key or not google_api_key or not deepseek_api_key or not groq_api_key:
        raise HTTPException(status_code=500, detail="One of your keys is not set.")

    # provider clients
    openaiClient = AsyncOpenAI()
    claudeClient = AsyncAnthropic()
    geminiClient = AsyncOpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    deepseekClient = AsyncOpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
    groqClient = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")

    seed_prompt = body.seed_prompt or (
        "Please come up with a challenging, nuanced question that I can ask a number "
        "of LLMs to evaluate their intelligence. Answer only with the question, no explanation."
    )

    # question = await generate_question(openaiClient, seed_prompt)

    competitors = body.competitors
    answers: List[str] = []
    models_and_clients = []

    for m in competitors:
        if m == "gpt-4o-mini":
            models_and_clients.append((m, openaiClient, query_gpt))
        elif m == "claude-3-7-sonnet-latest":
            models_and_clients.append((m, claudeClient, query_claude))
        elif m == "gemini-2.0-flash":
            models_and_clients.append((m, geminiClient, query_gpt))
        elif  m == "deepseek-chat":
            models_and_clients.append((m, deepseekClient, query_gpt))
        elif m == "llama-3.3-70b-versatile":
            models_and_clients.append((m, groqClient, query_gpt))
        else:
            raise HTTPException(status_code=400, detail="Unkown model: {m}")

    answers = await asyncio.gather(
        *[fn(client, seed_prompt, model_name) for (model_name, client, fn) in models_and_clients]
    )

    raw_ranking = await rank_responses(openaiClient, competitors, seed_prompt, answers)


    # rank models
    try:
        ranking_numbers = json.loads(raw_ranking)["results"]
    except Exception:
        raise HTTPException(status_code=502, detail=f"Judge returned malformed JSON: {raw_ranking}")

    # map indices back to model names
    ranking_models = [competitors[int(i) - 1] for i in ranking_numbers]

    # return answers
    return RankedResult(
        question=seed_prompt, 
        answers=[{"model": m, "answer": a} for m, a in zip(competitors, answers)], 
        ranking=ranking_models,
        raw_ranking_json=raw_ranking,
        )
