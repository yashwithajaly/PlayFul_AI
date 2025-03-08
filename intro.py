import tkinter as tk
import google.generativeai as genai
import random
import re

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCKTHB6eTWJcLKxDFNW0-FobprIivOdUfA")

# List of models and prompts
MODELS = [
    "gemini-1.5-pro", "gemini-1.5-pro-002", "gemini-1.5-pro-latest",
    "gemini-1.5-flash", "gemini-1.5-flash-002", "gemini-1.5-flash-latest"
]
PROMPTS = [
    "Give 1 surprising chess fact in just 2 lines.",
    "Tell me two fun chess trivia facts in 2 lines.",
    "Share two little-known chess facts in 2 lines."
]

class IntroScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game Intro")
        self.root.attributes('-fullscreen', True)  # Fullscreen mode
        self.root.configure(bg="#E3F2FD")  # Subtle background color

        # Main frame to center content
        self.frame = tk.Frame(root, bg="#E3F2FD")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # Header label
        self.label = tk.Label(
            self.frame, text="Welcome to Chess!", font=("Arial", 32, "bold"), bg="#E3F2FD", fg="#333"
        )
        self.label.pack(pady=20)

        # Start button
        self.start_button = tk.Button(
            self.frame, text="Start", font=("Arial", 20, "bold"), bg="#3498db", fg="black",
            activebackground="#2980b9", relief="flat", padx=20, pady=10, command=self.show_facts
        )
        self.start_button.pack(pady=10)

        # Facts label
        self.facts_label = tk.Label(
            self.frame, text="", wraplength=600, justify="center", font=("Georgia", 16, "italic"),
            bg="#E3F2FD", fg="#555"
        )
        self.facts_label.pack(pady=20)

        # Continue button (disabled initially)
        self.continue_button = tk.Button(
            self.frame, text="Continue to Game", font=("Arial", 20, "bold"), bg="#2ecc71", fg="black",
            activebackground="#27ae60", relief="flat", padx=20, pady=10, command=self.start_chess_game
        )
        self.continue_button.pack(pady=10)
        self.continue_button.config(state="disabled")

        # Exit button
        self.exit_button = tk.Button(
            self.frame, text="Exit", font=("Arial", 16, "bold"), bg="#e74c3c", fg="black",
            activebackground="#c0392b", relief="flat", padx=20, pady=5, command=root.destroy
        )
        self.exit_button.pack(pady=10)

    def show_facts(self):
        """Fetch and display interesting chess facts."""
        selected_model = random.choice(MODELS)
        selected_prompt = random.choice(PROMPTS)
        
        try:
            model = genai.GenerativeModel(selected_model, generation_config={"temperature": 0.9})
            response = model.generate_content(selected_prompt)
            facts = response.text.strip()
            facts = re.sub(r'\*\*|^\d+\.\s*|^[-*]\s*', '', facts, flags=re.MULTILINE)  # Clean formatting
            self.facts_label.config(text=f"Did you know?\n\n{facts}")
            self.continue_button.config(state="normal")
        except Exception as e:
            self.facts_label.config(text=f"Error fetching facts: {str(e)}")

    def start_chess_game(self):
        """Close this window and launch the chess game."""
        self.root.destroy()
        import chess_game
        chess_game.run_game()

if __name__ == "__main__":
    root = tk.Tk()
    IntroScreen(root)
    root.mainloop()