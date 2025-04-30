from get_pdf_from_input_folder import choose_pdf_from_input_folder
from preprocess_module import run_preprocessing
from generate_mcq_module import generate_mcqs_for_chunks
import os

def generate_mcqs_flow():
    # Step 1: Let user select a PDF from INPUT folder
    pdf_path = choose_pdf_from_input_folder()
    if not pdf_path:
        return  # Exit if no file selected

    # Step 2: Preprocess the selected PDF
    print("\n🚀 Starting preprocessing...")
    chunks = run_preprocessing(pdf_path)  # You must implement this function
    print("✅ Preprocessing complete.")
    
    # Step 3: Prompt user for number of MCQs
    while True:
        try:
            num_qs = int(input("\n🔢 How many MCQs per slide chunk (5 slides)?: ").strip())
            if 1 <= num_qs <= 10:
                break
            print("❌ Please enter a number between 1 and 10.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

    # Step 4: Generate MCQs
    print(f"🚀 Generating {num_qs} MCQs per chunk using GPT...")
    generate_mcqs_for_chunks(chunks, os.path.basename(pdf_path), num_qs=num_qs)
    print("🎉 MCQ generation complete!\n")
