import os

def choose_pdf_from_input_folder(input_dir="INPUT"):
    # Get all PDF files from the input directory
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("❌ No PDF files found in the INPUT folder.")
        return None

    # Display available files
    print("\n📂 Available Lecture PDFs:")
    for i, filename in enumerate(pdf_files, 1):
        print(f"{i}. {filename}")

    # Prompt user to choose
    while True:
        try:
            choice = int(input("\nEnter the number of the file to process: "))
            if 1 <= choice <= len(pdf_files):
                selected_file = pdf_files[choice - 1]
                print(f"\n✅ Selected file: {selected_file}")
                return os.path.join(input_dir, selected_file)
            else:
                print("❌ Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
