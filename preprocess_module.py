# preprocess_module.py

import fitz  # PyMuPDF
import json
from pathlib import Path

# Configuration
NEW_SLIDES = 4
CONTEXT_SLIDES = 1

def preprocess_pdf_chunks(pdf_path: Path):
    """
    Extract text from each slide and split into overlapping chunks.
    Returns a list of dicts: {chunk_id, pages, text}
    """
    doc = fitz.open(pdf_path)
    total = len(doc)
    slides = [page.get_text("text") for page in doc]

    chunks = []
    # First chunk
    first_end = min(NEW_SLIDES, total)
    first_pages = list(range(1, first_end + 1))
    chunks.append({
        "chunk_id": f"slides_1_{first_end}",
        "pages": first_pages,
        "text": "\n".join(slides[i - 1] for i in first_pages)
    })

    # Subsequent chunks
    start = first_end + 1
    while start <= total:
        context_page = start - CONTEXT_SLIDES
        end = min(start + NEW_SLIDES - 1, total)
        pages = [context_page] + list(range(start, end + 1))
        chunks.append({
            "chunk_id": f"slides_{pages[0]}_{pages[-1]}",
            "pages": pages,
            "text": "\n".join(slides[i - 1] for i in pages)
        })
        start += NEW_SLIDES

    return chunks

def run_preprocessing(pdf_path_str):
    """
    Used by generate_mcqs_flow(). Takes one PDF path as input, returns list of chunks.
    """
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    print(f"📄 Preprocessing: {pdf_path.name}")
    return preprocess_pdf_chunks(pdf_path)

# Optional: keep batch mode for dev/debugging
def preprocess_all_pdfs(input_dir: Path, output_dir: Path):
    """
    Batch-mode: process all PDFs in input_dir and save to output_dir.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    for pdf_file in sorted(input_dir.glob("*.pdf")):
        chunks = preprocess_pdf_chunks(pdf_file)
        out_file = output_dir / f"{pdf_file.stem}_chunks.json"
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"Processed '{pdf_file.name}': {len(chunks)} chunks → {out_file}")

if __name__ == "__main__":
    preprocess_all_pdfs("INPUT", "OUTPUT")