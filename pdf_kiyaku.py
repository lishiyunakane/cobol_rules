import os
import time
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-05-01-preview"
)

def create_vector_store():
    return client.beta.vector_stores.create(name="Azure GPT-4.1-mini PDF Store")

def upload_pdf(file_path, vector_store_id):
    with open(file_path, "rb") as f:
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=[f]
        )
    return file_batch

def create_assistant(vector_store_id):
    assistant = client.beta.assistants.create(
        name="PDF Summarizer (Azure GPT-4.1-mini)",
        instructions="You are a helpful assistant that specializes in reading and summarizing PDFs.",
        model="gpt-4.1-mini",  
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
    )
    return assistant

def pdf_summarize(assistant_id, question):
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            raise RuntimeError("Assistant run failed.")
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def save_to_json(content: str, filename: str):
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print("❌ Error: Output is not valid JSON.")
        raise e

    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved to: {filepath}")


if __name__ == "__main__":
    file_path = os.path.join(os.path.dirname(__file__), "sample.pdf")

    vector_store = create_vector_store()
    upload_pdf(file_path, vector_store.id)

    assistant = create_assistant(vector_store.id)

    prompt = """
    You are an assistant that summarizes coding conventions found in a PDF document. The target is to extract and organize all E-Cobol coding standards described in the file.

    Please carefully read through the entire PDF and identify each distinct rule or convention related to E-Cobol programming. For each rule you find, extract the following:

    - A brief summary of what the rule is about (in your own words)
    - The original wording of the rule as written in the PDF
    - One representative example, if any are provided. If no example is given, use an **empty string** ("").

    Output your result strictly as a **JSON array**, where each item follows this exact structure:

    {
    "rule_title": "Summary of the rule (your wording)",
    "rule_text": "The original text from the PDF",
    "example": "One example if provided, otherwise use an empty string \"\""
    }

    ⚠️ Very important:
    - Do **not** include any explanations, comments, markdown code fences (like ```), or natural language before or after the JSON.
    - Your output must be valid, parsable JSON **only**.
    """

    summary = pdf_summarize(assistant.id, prompt)
    save_to_json(summary, "coding_kiyaku_4.1mini.json")
