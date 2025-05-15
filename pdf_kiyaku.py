import os
import json
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

if os.getenv("gpt") is not None:
    client = OpenAI(api_key=os.getenv("gpt"))

def extract_text_by_page(file_path):
    page_texts = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = f"\n--- Page {page_num} ---\n"

            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table and len(table) > 1:
                        headers = table[0]
                        text += "| " + " | ".join(headers) + " |\n"
                        text += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                        for row in table[1:]:
                            row_clean = [cell.strip() if cell else "" for cell in row]
                            text += "| " + " | ".join(row_clean) + " |\n"
                        text += "\n"

            page_text_raw = page.extract_text(x_tolerance=1, y_tolerance=1, layout=True)
            if page_text_raw:
                text += page_text_raw.strip()

            page_texts.append(text)
    return page_texts

def remove_known_headers_footers(lines):
    cleaned_lines = []
    for line in lines:
        if any(keyword in line for keyword in [
            "営業秘密", "E-COBOL コーディング規約書", "発行部署", "発行日", "版数", "改訂日", "文書番号", "印刷日", "第二開一"
        ]):
            continue
        if "Copyright" in line or "NTT DATA CORPORATION" in line:
            continue
        cleaned_lines.append(line)
    return cleaned_lines

def clean_extracted_pages(pages):
    cleaned = []
    for page in pages:
        lines = page.splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        lines = remove_known_headers_footers(lines)
        cleaned.append("\n".join(lines))
    return cleaned

def batch_pages(pages, batch_size=5):
    return [pages[i:i+batch_size] for i in range(0, len(pages), batch_size)]

def summarize_batch(batch_text, instruction):
    clipped_text = "\n\n".join(batch_text)[:6000]
    full_prompt = f"{instruction}\n\n{clipped_text}"
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()

    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print("Error JSON format：", content[:300])
        raise e

def save_to_json(content, filename="summary.json"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"successfully saved JSON：{filename}")

if __name__ == "__main__":
    pdf_path = os.path.join(os.path.dirname(__file__), "sample.pdf")

    print("Extracting PDF...")
    all_pages = extract_text_by_page(pdf_path)
    cleaned_pages = clean_extracted_pages(all_pages)
    page_batches = batch_pages(cleaned_pages, batch_size=5)

    prompt = """
    You are a highly accurate assistant specialized in analyzing technical documents and summarizing programming conventions.

    Your task is to read through the **entire PDF** and extract all coding rules, standards, or best practices related to **E-Cobol programming**.

    For each distinct rule you find, extract the following:

    - "rule_title": A brief summary of what the rule is about (written in your own words, in plain English)
    - "rule_text": The original expression of the rule as described in the PDF
    - "example": One representative example if any are provided; if no example exists, set this field to an empty string ""

    ⚠️ Very important:
    - You must carefully read and analyze the entire PDF document, not just retrieve the most relevant sections.
    - Return your output as a valid JSON array, where each item follows this structure:
    {
    "rule_title": "（日本語）",
    "rule_text": "（日本語原文）",
    "example": "（日本語例文 or \"\"）"
    }
    - Do not include any additional explanation, natural language commentary, or Markdown code fences (like ```).
    - Your response must be strictly valid JSON and parsable by standard JSON parsers.

    Make sure the output includes all identified rules, even if they are spread across different parts of the PDF.
    """

    print(" GPT に送信して規約を抽出中...")
    final_results = []
    for idx, batch in enumerate(page_batches, start=1):
        print(f"🔄 Batch {idx}/{len(page_batches)}")
        try:
            result = summarize_batch(batch, prompt)
            final_results.extend(result)
        except Exception as e:
            print(f" Batch {idx} failed:", e)

    save_to_json(final_results, "summary_gpt4.1mini_all.json")
