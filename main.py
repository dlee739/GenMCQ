# main.py

def show_welcome():
    print("=" * 60)
    print("\n\n🧠 Welcome to the MCQ Assistant for Medical Lectures 🧠")
    print("=" * 60)

def show_main_menu():
    print("\nPlease choose an option:")
    print("1. Generate MCQs from Lecture Script")
    print("2. Take a Quiz using Existing MCQs")
    print("Q. Quit")

def main():
    show_welcome()

    while True:
        show_main_menu()
        choice = input("\nEnter your choice (1/2 or Q to quit): ").strip().lower()

        if choice == "1":
            from generate_mcqs import generate_mcqs_flow
            generate_mcqs_flow()
        elif choice == "2":
            from run_quiz import run_quiz_flow
            run_quiz_flow()
        elif choice == "q":
            print("👋 Exiting. Have a great day!\n\n\n")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or Q.")

if __name__ == "__main__":
    main()
