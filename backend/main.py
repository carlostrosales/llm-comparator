import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
# from IPython.display import Markdown, display

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set (and this is optional)")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:2]}")
else:
    print("Google API Key not set (and this is optional)")

if deepseek_api_key:
    print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
else:
    print("DeepSeek API Key not set (and this is optional)")

if groq_api_key:
    print(f"Groq API Key exists and begins {groq_api_key[:4]}")
else:
    print("Groq API Key not set (and this is optional)")


print("\n\n\n\n\n\n")


request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
request += "Answer only with the question, no explanation."

messages=[{"role": "user", "content": request}]

openai = OpenAI()
response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
question = response.choices[0].message.content
# print(question + "\n\n\n\n\n\n")

competitors = []
answers = []
messages=[{"role": "user", "content": question}]


# first answer from model 1
model_name = "gpt-4o-mini"
response = openai.chat.completions.create(model=model_name,messages=messages)
answer = response.choices[0].message.content
# print(answer + "\n\n\n\n\n\n")

competitors.append(model_name)
answers.append(answer)

# second answer from model 2
model_name = "claude-3-7-sonnet-latest"
claude = Anthropic()
response = claude.messages.create(model=model_name, messages=messages, max_tokens=1000)
answer = response.content[0].text
# print(answer + "\n\n\n\n\n\n")

competitors.append(model_name)
answers.append(answer)

# third answer from model 3
model_name = "gemini-2.0-flash"
gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
response = gemini.chat.completions.create(model=model_name,messages=messages)
answer = response.choices[0].message.content
# print(answer + "\n\n\n\n\n\n")

competitors.append(model_name)
answers.append(answer)

# fourth answer from model 4
model_name="deepseek-chat"
deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
response = deepseek.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content
# print(answer + "\n\n\n\n\n\n")

competitors.append(model_name)
answers.append(answer)


# fifth answer from model 5
model_name = "llama-3.3-70b-versatile"
groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
response = groq.chat.completions.create(model=model_name, messages=messages)
answer = response.choices[0].message.content
# print(answer + "\n\n\n\n\n\n")

competitors.append(model_name)
answers.append(answer)



together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index + 1}\n\n"
    together += answer + "\n\n"

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
openai = OpenAI()
openai = OpenAI()
response = openai.chat.completions.create(
    model="o3-mini",
    messages=judge_messages,
)
results = response.choices[0].message.content

# Turn into readable results
results_dict = json.loads(results)
ranks = results_dict["results"]
for index, result in enumerate(ranks):
    competitor = competitors[int(result) - 1]
    print(f"Rank {index+1}: {competitor}")


def main():
    print("Script setup.")

if __name__== "__main__":
    main()