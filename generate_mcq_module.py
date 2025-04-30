import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load API key from .env
load_dotenv()
client = OpenAI()

# Output folder
MCQ_JSON_DIR = Path("MCQ_OUTPUT")
MCQ_JSON_DIR.mkdir(exist_ok=True)

# Prompt templates
SYSTEM_PROMPT = (
    "You are an expert exam writer creating clear, fair multiple-choice questions "
    "based on slide content. Focus on conceptual understanding."
)

USER_PROMPT_TEMPLATE = (
    "Here is the text of five consecutive slides (first is context):\n\n"
    "{chunk_text}\n\n"
    "{prompt_details}\n\n"
    "Generate {num_qs} MCQs. For each question:\n"
    "1. A question stem.\n"
    "2. Four options labeled A–D.\n"
    "3. Identify the correct option.\n\n"
    "Return a valid JSON list in this format:\n"
    "[\n"
    "  {{ 'id': 1, 'question': '...', 'options': {{ 'A': '...', 'B': '...', 'C': '...', 'D': '...' }}, 'answer': 'C' }},\n"
    "  ...\n"
    "]"
)

def load_prompt_details(file_path="MCQ_PROMPT.txt") -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("⚠️ MCQ_PROMPT.txt not found. Continuing with default prompt only.")
        return ""

def extract_json_from_response(content: str) -> str:
    match = re.search(r"```(?:json)?\s*(.+?)\s*```", content, flags=re.DOTALL)
    return match.group(1).strip() if match else content.strip()

def generate_mcqs_for_chunk(text: str, num_qs: int = 4, max_retries: int = 2):
    prompt_details = load_prompt_details()
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
            chunk_text=text,
            num_qs=num_qs,
            prompt_details=prompt_details
        )}
    ]

    for attempt in range(1, max_retries + 1):
        print(f"[Attempt {attempt}] Calling GPT...")
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=700,
            timeout=30
        )
        content = resp.choices[0].message.content.strip()
        clean_content = extract_json_from_response(content)

        try:
            return json.loads(clean_content)
        except json.JSONDecodeError:
            print(f"[Attempt {attempt}] Invalid JSON. Requesting correction...")
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "Only output pure valid JSON array. No explanations."})

    raise ValueError("❌ Failed to generate valid JSON after retries.")

def generate_mcqs_for_chunks(chunks: list, pdf_filename: str, num_qs: int = 4):
    """
    Generates MCQs for a list of chunks and saves them to a file.
    """
    stem = Path(pdf_filename).stem
    all_mcqs = {}

    for chunk in chunks:
        cid = chunk["chunk_id"]
        text = chunk["text"]
        print(f"[INFO] Generating MCQs for {cid} ({len(text.split())} words)...")
        all_mcqs[cid] = generate_mcqs_for_chunk(text, num_qs=num_qs)

    # Save output
    out_path = MCQ_JSON_DIR / f"{stem}_mcqs.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(all_mcqs, f, indent=2, ensure_ascii=False)

    print(f"✅ MCQs saved to: {out_path}")
