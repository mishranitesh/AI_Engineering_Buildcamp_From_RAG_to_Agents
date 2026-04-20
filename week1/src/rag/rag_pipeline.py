import json
import tiktoken
import os

#from openai import OpenAI

# Create OpenAI client
# This automatically reads OPENAI_API_KEY from your environment
#openai_client = OpenAI()

# System instructions for the assistant
instructions = """
You're a course assistant, your task is to answer the QUESTION from the
course students using the provided CONTEXT
""".strip()


# Prompt template used for the final LLM call
prompt_template = """
<QUESTION>
{question}
</QUESTION>

<CONTEXT>
{context}
</CONTEXT>
""".strip()

from pydantic import BaseModel, Field
from typing import Literal


class RAGResponse(BaseModel):
    """
    Structured schema for the RAG answer.
    """

    answer: str = Field(
        description="The main answer to the user's question in markdown"
    )
    found_answer: bool = Field(
        description="True if relevant information was found in the documentation"
    )
    confidence: float = Field(
        description="Confidence score from 0.0 to 1.0"
    )
    confidence_explanation: str = Field(
        description="Explanation about the confidence level"
    )
    answer_type: Literal[
        "how-to",
        "explanation",
        "troubleshooting",
        "comparison",
        "reference"
    ] = Field(
        description="The category of the answer"
    )
    followup_questions: list[str] = Field(
        description="Suggested follow-up questions"
    )

def build_prompt(question, search_results):
    """
    Build the user prompt for the LLM.

    What this does:
    1. Converts search results into formatted JSON
    2. Injects the question and context into the template
    3. Returns the final prompt string
    """

    # Convert retrieved chunks into pretty JSON text
    context = json.dumps(search_results, indent=2)

    # Fill the prompt template
    prompt = prompt_template.format(
        question=question,
        context=context
    ).strip()

    return prompt


def search(index, question):
    """
    Search the minsearch index and return top 5 chunks.
    """

    return index.search(question, num_results=5)

'''
def llm(user_prompt, instructions, model="gpt-4o-mini"):
    """
    Send the prompt to the LLM and return:
    - answer text
    - input tokens
    - output tokens

    OpenAI Responses API returns token usage in response.usage.
    """

    # Messages passed to the model
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt}
    ]

    # Call the model
    response = openai_client.responses.create(
        model=model,
        input=messages
    )

    # Extract text output
    answer = response.output_text

    # Extract token usage
    # Current OpenAI docs expose usage information on the response object
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    return answer, input_tokens, output_tokens

import google.generativeai as genai
import os


# Configure Gemini with API key from environment
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
'''

'''
from openai import OpenAI

openai_client = OpenAI()


def llm_structured(user_prompt, instructions, model="gpt-4o-mini"):
    """
    Call the LLM using structured outputs.

    Returns:
    - parsed structured object
    - input tokens
    - output tokens
    """

    # Build chat-style messages
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt}
    ]

    # Use OpenAI structured output parsing
    response = openai_client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=RAGResponse,
    )

    # Parsed structured result as a Pydantic object
    parsed_output = response.choices[0].message.parsed

    # Token usage from the API response
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    return parsed_output, input_tokens, output_tokens
'''

import json
import tiktoken


def llm_structured(user_prompt, instructions):
    """
    Estimate structured-output input tokens locally using tiktoken.

    This does not call an LLM.
    It estimates the extra schema overhead that structured output adds.
    """

    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    # Base input used in Q5
    base_text = instructions + "\n\n" + user_prompt
    base_tokens = len(enc.encode(base_text))

    # Add schema text to simulate structured-output overhead
    schema_text = json.dumps(RAGResponse.model_json_schema(), indent=2)

    structured_text = base_text + "\n\n" + schema_text
    structured_tokens = len(enc.encode(structured_text))

    return base_tokens, structured_tokens, structured_tokens - base_tokens


def llm(user_prompt, instructions, model=None):
    """
    Token-counting version of LLM (no API call).

    This is sufficient for homework:
    - counts input tokens accurately
    - returns mock answer
    """

    # Load tokenizer for GPT model
    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    # Count tokens for:
    # system instructions + user prompt
    input_tokens = (
        len(enc.encode(instructions)) +
        len(enc.encode(user_prompt))
    )

    # Mock answer (content doesn't matter for homework)
    answer = "A function in Python is defined using the def keyword."

    # Count output tokens
    output_tokens = len(enc.encode(answer))

    return answer, input_tokens, output_tokens


def rag(index, query):
    """
    Full RAG pipeline:
    1. Search
    2. Build prompt
    3. Call LLM
    4. Return answer and token counts
    """

    # Retrieve relevant chunks
    search_results = search(index, query)

    # Build final prompt
    prompt = build_prompt(query, search_results)

    # Call the model
    answer, input_tokens, output_tokens = llm(prompt, instructions)

    return {
        "query": query,
        "search_results": search_results,
        "prompt": prompt,
        "answer": answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }

def rag_structured(index, query):
    """
    Full RAG pipeline using structured output.

    Steps:
    1. Retrieve search results
    2. Build the prompt
    3. Ask the model for a structured response
    4. Return both the structured object and token counts
    """

    # Retrieve top results from the index
    search_results = search(index, query)

    # Build the final prompt with QUESTION + CONTEXT
    prompt = build_prompt(query, search_results)

    # Call structured LLM
    structured_answer, input_tokens, output_tokens = llm_structured(
        prompt,
        instructions
    )

    return {
        "query": query,
        "search_results": search_results,
        "prompt": prompt,
        "structured_answer": structured_answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }