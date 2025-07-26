import os
import json
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI, APIStatusError
from anthropic import AsyncAnthropic

load_dotenv(override=True)

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
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI API error ({e.status.code}): {e.message}") from e

async def query_claude(client: AsyncAnthropic, question: str, model_name: str) -> str:
    try:
        resp = await client.messages.create(model=model_name, messages=[{"role": "user", "content": question}], max_tokens=1000)
        return resp.content[0].text.strip()
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI API error ({e.status.code}): {e.message}") from e

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


async def main():
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')

    if not openai_api_key or not anthropic_api_key or not google_api_key or not deepseek_api_key or not groq_api_key:
        raise RuntimeError("One of your keys are not set.")

    client = AsyncOpenAI()

    seed_prompt = (
        "Please come up with a challenging, nuanced question that I can ask a number "
        "of LLMs to evaluate their intelligence. Answer only with the question, no explanation."
    )

    question = await generate_question(client, seed_prompt)
    print("Generated Question: \n\n\n", question)

    competitors = []
    answers = []

    # first answer from model
    gptMini = "gpt-4o-mini"
    answer = await query_gpt(client, question, gptMini)
    competitors.append(gptMini)
    answers.append(answer)

    # second answer from model
    claude = "claude-3-7-sonnet-latest"
    claudeClient = AsyncAnthropic()
    answer = await query_claude(claudeClient, question, claude)
    competitors.append(claude)
    answers.append(answer)

    # third answer from model
    gemini = "gemini-2.0-flash"
    geminiClient = AsyncOpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    answer = await query_gpt(geminiClient, question, gemini)
    competitors.append(gemini)
    answers.append(answer)

    # fourth answer from model
    deepseek="deepseek-chat"
    deepseekClient = AsyncOpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
    answer = await query_gpt(deepseekClient, question, deepseek)
    competitors.append(deepseek)
    answers.append(answer)

    # fifth answer from model
    llama = "llama-3.3-70b-versatile"
    groqClient = AsyncOpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
    answer = await query_gpt(groqClient, question, llama)
    competitors.append(llama)
    answers.append(answer)

    # format all llm answers
    formattedAnswers = await format_responses(answers)

    # rank llm answers
    rankedAnswers = await rank_responses(client, competitors, question, formattedAnswers)

    # print answers
    await print_rankings(rankedAnswers, competitors)



if __name__== "__main__":
    asyncio.run(main())