import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from pathlib import Path
import textwrap
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

GPT_SYSTEM_PROMPT = (
    "You are a medical tutor helping students understand quiz questions."
)

GPT_USER_PROMPT_TEMPLATE = (
    "A student answered a multiple-choice question incorrectly. Here is the full question:\n\n"
    "Question: {question}\n"
    "Options:\n"
    "{options_text}\n\n"
    "Correct Answer: {correct}\n"
    "Student's Answer: {wrong}\n\n"
    "Please explain in 2–3 sentences:\n"
    "1. Why the correct answer is right.\n"
    "2. Why the student's selected answer is wrong."
)

def format_options(options):
    return "\n".join(f"{k}. {v}" for k, v in options.items())

def get_gpt_explanation(question, options, correct, user):
    """
    Given the question, options, correct answer, and user answer,
    ask GPT for a short explanation.
    """
    user_prompt = GPT_USER_PROMPT_TEMPLATE.format(
        question=question,
        options_text=format_options(options),
        correct=correct,
        wrong=user
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )

    return response.choices[0].message.content.strip()



def draw_wrapped_text(c, text, x, y, max_width=90, line_height=15):
    """
    Draw wrapped text on the canvas at (x, y).
    - max_width is in number of characters (not pixels)
    - returns updated y position after drawing
    """
    wrapped = textwrap.wrap(text, width=max_width)
    for line in wrapped:
        if y < 100:
            c.showPage()
            y = LETTER[1] - 50
            c.setFont("Helvetica", 12)
        c.drawString(x, y, line)
        y -= line_height
    return y


def create_pdf_canvas(title_prefix="RESULTS"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{title_prefix} - {timestamp}.pdf"
    filepath = Path("REPORTS") / filename
    filepath.parent.mkdir(exist_ok=True)

    c = canvas.Canvas(str(filepath), pagesize=LETTER)
    width, height = LETTER
    c.setTitle(filename)
    return c, filepath

def write_basic_report_to_pdf(user_answers):
    c, filepath = create_pdf_canvas()

    width, height = LETTER
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Quiz Report")
    c.setFont("Helvetica", 12)
    y -= 30

    for idx, ans in enumerate(user_answers, 1):
        q = f"{idx}. {ans['question']}"
        ua = ans['user_answer'] or "Skipped"
        ca = ans['correct_answer']
        result = "Correct" if ans['is_correct'] else "Incorrect"

        # Draw question
        y = draw_wrapped_text(c, q, x=50, y=y)

        # Draw options A–D
        for key, text in ans["options"].items():
            option_line = f"{key}. {text}"
            y = draw_wrapped_text(c, option_line, x=60, y=y)

        # Draw answers and result
        y = draw_wrapped_text(c, f"Your Answer: {ua}", x=50, y=y)
        y = draw_wrapped_text(c, f"Correct Answer: {ca}", x=50, y=y)
        y = draw_wrapped_text(c, f"Result: {result}", x=50, y=y)

        # Add space before next question
        y -= 20


    c.save()
    print(f"\n📄 Report saved to: {filepath}")

def write_detailed_report_to_pdf(user_answers):
    c, filepath = create_pdf_canvas("DETAILED RESULTS")
    width, height = LETTER
    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Detailed Quiz Report (with GPT)")
    c.setFont("Helvetica", 12)
    y -= 30

    for idx, ans in enumerate(user_answers, 1):
        q = f"{idx}. {ans['question']}"
        ua = ans['user_answer'] or "Skipped"
        ca = ans['correct_answer']
        result_text = "Correct" if ans["is_correct"] else "Incorrect"

        # Bold question
        c.setFont("Helvetica-Bold", 12)
        y = draw_wrapped_text(c, q, x=50, y=y)
        c.setFont("Helvetica", 12)

        # Show options A–D
        for key, text in ans["options"].items():
            y = draw_wrapped_text(c, f"{key}. {text}", x=60, y=y)

        # Highlight user and correct answers
        c.setFont("Helvetica-Bold", 12)
        y = draw_wrapped_text(c, f"Your Answer: {ua}", x=50, y=y)
        y = draw_wrapped_text(c, f"Correct Answer: {ca}", x=50, y=y)
        y = draw_wrapped_text(c, f"Result: {result_text}", x=50, y=y)
        c.setFont("Helvetica", 12)

        # Explanation for incorrect
        if not ans["is_correct"]:
            c.setFont("Helvetica-Bold", 12)
            y = draw_wrapped_text(c, "Explanation:", x=50, y=y)
            c.setFont("Helvetica", 12)
            explanation = get_gpt_explanation(
                question=ans["question"],
                options=ans["options"],
                correct=ans["correct_answer"],
                user=ans["user_answer"] or "Skipped"
            )
            y = draw_wrapped_text(c, explanation, x=60, y=y)

        # Space between questions
        y -= 25

    c.save()
    print(f"\n📄 Detailed report saved to: {filepath}")




def select_mcq_file(mcq_dir="MCQ_OUTPUT"):
    # Get all .json MCQ files from the output directory
    mcq_files = [f for f in os.listdir(mcq_dir) if f.lower().endswith(".json")]

    if not mcq_files:
        print("❌ No MCQ files found in MCQ_OUTPUT.")
        return None

    # Display file options
    print("\n📚 Available MCQ Sets:")
    for i, filename in enumerate(mcq_files, 1):
        print(f"{i}. {filename}")

    # Prompt user to choose
    while True:
        try:
            choice = int(input("\nEnter the number of the file to quiz on: "))
            if 1 <= choice <= len(mcq_files):
                selected = mcq_files[choice - 1]
                print(f"\n✅ Selected: {selected}")
                return os.path.join(mcq_dir, selected)
            else:
                print("❌ Invalid number. Try again.")
        except ValueError:
            print("❌ Please enter a valid number.")

def load_mcqs(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten all chunks into one list of questions
    all_questions = []
    for chunk_id, question_list in data.items():
        for q in question_list:
            q["chunk_id"] = chunk_id  # preserve metadata
            all_questions.append(q)

    return all_questions

def run_quiz_session(mcqs):
    print(f"\n🧪 Starting quiz: {len(mcqs)} questions total.")
    print("Type A, B, C, or D to answer. Type 'skip' to skip a question.\n")

    user_answers = []

    for idx, question in enumerate(mcqs, 1):
        print(f"\n📖 Question {idx} of {len(mcqs)}")
        print(question["question"])
        for letter, text in question["options"].items():
            print(f"  {letter}. {text}")

        # Input loop
        while True:
            response = input("Your answer (A/B/C/D or skip): ").strip().upper()
            if response in ["A", "B", "C", "D", "SKIP"]:
                break
            print("❌ Invalid input. Please enter A, B, C, D, or 'skip'.")

        user_answers.append({
            "question_id": question["id"],
            "chunk_id": question["chunk_id"],
            "question": question["question"],
            "options": question["options"],
            "correct_answer": question["answer"],
            "user_answer": None if response == "SKIP" else response,
            "skipped": response == "SKIP",
            "is_correct": (response == question["answer"]) if response != "SKIP" else False
        })  


    print("\n✅ Quiz complete.")
    return user_answers

def post_quiz_menu(user_answers):
    print("\n📋 Choose a report type:")
    print("1. Normal report (no GPT)")
    print("2. Detailed report with GPT explanations for incorrect answers")
    print("Q. Quit")

    while True:
        choice = input("Enter your choice (1/2 or Q): ").strip().lower()
        if choice in ["1", "2", "q"]:
            return choice
        print("❌ Invalid input. Please enter 1, 2, or Q.")

def print_basic_report(user_answers):
    print("\n🧾 BASIC REPORT\n" + "=" * 60)
    for idx, ans in enumerate(user_answers, 1):
        print(f"\n{idx}. {ans['question']}")
        for key, text in ans["options"].items():
            print(f"   {key}. {text}")
        print(f"🔹 Your Answer: {ans['user_answer'] or 'Skipped'}")
        print(f"✅ Correct Answer: {ans['correct_answer']}")
        status = "✅ Correct" if ans["is_correct"] else "❌ Incorrect"
        print(f"Result: {status}")



def run_quiz_flow():
    file_path = select_mcq_file()
    if not file_path:
        return

    mcqs = load_mcqs(file_path)
    user_answers = run_quiz_session(mcqs)

    # Placeholder for next step
    print("\n📊 Calculating results...")
    correct = sum(1 for a in user_answers if a["is_correct"])
    print(f"\n📝 Your Score: {correct}/{len(user_answers)} correct ({(correct/len(user_answers))*100:.1f}%)")

    # Step 3: to be implemented
    choice = post_quiz_menu(user_answers)
    if choice == "1":
        write_basic_report_to_pdf(user_answers)
    elif choice == "2":
        write_detailed_report_to_pdf(user_answers)
    elif choice == "q":
        print("👋 Exiting to main menu.")

