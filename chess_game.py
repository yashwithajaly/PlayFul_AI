import tkinter as tk
from tkinter import messagebox, scrolledtext
import chess
import chess.engine
import random
import google.generativeai as genai

# Configure Gemini API Key (replace with your actual key)
genai.configure(api_key="Your api key")

# Lc0 engine path
ENGINE_PATH = "/usr/local/bin/lc0"

# Weights paths
WEIGHTS = {
    "aggressive": "aggressive.pb",
    "balanced": "/opt/homebrew/Cellar/lc0/0.31.2/share/lc0/weights/42850",
    "defensive": "defensive.pb",
}

# Start LC0 engine
engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

def analyze_player_moves(player_moves):
    """Analyze the user's first 3 moves to decide if they're aggressive, defensive, or balanced."""
    aggressive_squares = {"e4", "d4", "c4", "f4", "g4"}
    defensive_squares = {"e3", "d3", "g3", "b3", "h3"}
    aggressive_count = sum(1 for move in player_moves if move[2:4] in aggressive_squares)
    defensive_count = sum(1 for move in player_moves if move[2:4] in defensive_squares)
    if aggressive_count >= 2:
        return "aggressive"
    elif defensive_count >= 2:
        return "defensive"
    else:
        return "balanced"

def get_best_move(board, time_limit):
    """Ask LC0 for its best move given a time limit."""
    result = engine.play(board, chess.engine.Limit(time=10))
    return result.move.uci()

def explain_ai_move(fen, move):
    """Generate an explanation for the AI's move using Gemini."""
    prompt = f"Chess board position: {fen}. AI played {move}. Why is this a strong move based on the position?"
    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error in explanation: {str(e)}"

def suggest_best_moves(board, last_player_move):
    """Suggest the top 3 moves the user could have played, with explanations from Gemini."""
    analysis = engine.analyse(board, chess.engine.Limit(time=1.0), multipv=3)
    best_moves = [(info["pv"][0].uci(), info["score"].relative.score()) for info in analysis]
    explanations = []
    model = genai.GenerativeModel("gemini-1.5-flash")
    for move, _ in best_moves:
        prompt = (f"Chess position: {board.fen()}. The player moved {last_player_move}, "
                  f"but a stronger move was {move}. Explain in 1 line why {move} is a better choice based on future moves prediction and it should be short and simple for even 8 year old to understand. ")
        try:
            response = model.generate_content(prompt)
            explanation = response.text.strip()
        except Exception as e:
            explanation = f"Error generating explanation: {str(e)}"
        explanations.append((move, explanation))
    return explanations

# Mapping piece symbols (from python-chess) to Unicode
piece_to_unicode = {
    "P": "♙", "R": "♖", "N": "♘", "B": "♗", "Q": "♕", "K": "♔",
    "p": "♟", "r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚"
}

class ChessGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game with AI")
        self.player_side = None
        self.choose_side()

        # Create a python-chess board
        self.board = chess.Board()
        self.player_moves = []  # Records UCI moves from the user
        self.ai_moves = []
        self.ai_style = None

        # Create UI components
        self.create_board_ui()
        self.create_info_panel()
        self.selected_square = None  # Holds UCI square (e.g., "e2") when selecting a move

        self.update_board_ui()

        # If user chose Black, AI (White) should move first
        if self.player_side == "Black":
            self.root.after(500, self.ai_move)

    def choose_side(self):
        """Popup to choose White or Black side."""
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Choose Your Side")
        tk.Label(choice_window, text="Choose your side:").pack(pady=10)
        btn_white = tk.Button(choice_window, text="White", width=10,
                              command=lambda: self.set_side("White", choice_window))
        btn_white.pack(side=tk.LEFT, padx=10, pady=10)
        btn_black = tk.Button(choice_window, text="Black", width=10,
                              command=lambda: self.set_side("Black", choice_window))
        btn_black.pack(side=tk.RIGHT, padx=10, pady=10)
        self.root.wait_window(choice_window)

    def set_side(self, side, window):
        self.player_side = side
        window.destroy()

    def create_board_ui(self):
        """Create a 10x10 grid: 
           - top row has file labels (a..h)
           - left column has rank labels (8..1 if White, 1..8 if Black)
           - board squares in the 8x8 center
        """
        self.board_frame = tk.Frame(self.root)
        self.board_frame.pack(side=tk.LEFT, padx=10)

        # We'll store labels in a 2D list, but note that row/col 0 or 9 are for labels
        self.labels = [[None for _ in range(9)] for _ in range(9)]

        for row in range(9):
            for col in range(9):
                # Top-left corner is blank
                if row == 0 and col == 0:
                    label = tk.Label(self.board_frame, text="", width=3, height=1)
                    label.grid(row=row, column=col)
                    self.labels[row][col] = label
                    continue

                # Top row: file labels
                if row == 0 and col > 0:
                    file_char = chr(ord('a') + col - 1)
                    if self.player_side == "Black":
                        file_char = chr(ord('h') - (col - 1))
                    label = tk.Label(self.board_frame, text=file_char, width=3, height=1, font=("Arial", 12, "bold"))
                    label.grid(row=row, column=col)
                    self.labels[row][col] = label
                    continue

                # Left column: rank labels
                if col == 0 and row > 0:
                    rank_num = 9 - row  # if White
                    if self.player_side == "Black":
                        rank_num = row
                    label = tk.Label(self.board_frame, text=str(rank_num), width=3, height=1, font=("Arial", 12, "bold"))
                    label.grid(row=row, column=col)
                    self.labels[row][col] = label
                    continue

                # Board squares: row/col offset by 1
                board_row = row - 1
                board_col = col - 1
                color = "#DDB88C" if (board_row + board_col) % 2 == 0 else "#A66D4F"
                label = tk.Label(self.board_frame, text="", font=("Arial", 32),
                                 width=2, height=1, bg=color, relief="ridge")
                label.grid(row=row, column=col)
                label.bind("<Button-1>", lambda e, r=board_row, c=board_col: self.on_square_click(r, c))
                self.labels[row][col] = label

    def create_info_panel(self):
        """Create a panel on the right with AI explanation and move suggestions."""
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(side=tk.RIGHT, padx=10, fill=tk.BOTH)
        # tk.Label(self.info_frame, text="AI Explanation", font=("Arial", 14)).pack(pady=5)
        # self.ai_explanation = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD, width=40, height=10)
        # self.ai_explanation.pack(pady=5)
        tk.Label(self.info_frame, text="Move Suggestions", font=("Arial", 14)).pack(pady=5)
        self.suggestion_text = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD, width=40, height=10)
        self.suggestion_text.pack(pady=5)
        # tk.Label(self.info_frame, text="Killed Coins", font=("Arial", 14)).pack(pady=5)
        # self.killed_coins_text = scrolledtext.ScrolledText(self.info_frame, wrap=tk.WORD, width=40, height=5)
        # self.killed_coins_text.pack(pady=5)
    def gui_to_uci(self, row, col):
        """Convert GUI board row/col (0..7) to a UCI square (e.g., 'e2')."""
        if self.player_side == "White":
            file = chr(ord('a') + col)
            rank = str(8 - row)
        else:  # Black perspective: flip
            file = chr(ord('a') + (7 - col))
            rank = str(row + 1)
        return file + rank

    def update_board_ui(self):
        """Refresh the 8x8 board squares (which are offset by +1 in our grid)."""
        for row in range(8):
            for col in range(8):
                uci_sq = self.gui_to_uci(row, col)
                square = chess.parse_square(uci_sq)
                piece = self.board.piece_at(square)
                board_label = self.labels[row+1][col+1]
                if piece:
                    board_label.config(text=piece_to_unicode.get(piece.symbol(), piece.symbol()))
                else:
                    board_label.config(text="")

    def on_square_click(self, row, col):
        """Handle a player's click on the board (row,col in 0..7)."""
        square = self.gui_to_uci(row, col)
        if self.selected_square is None:
            # Attempting to select a piece
            piece = self.board.piece_at(chess.parse_square(square))
            if piece:
                if ((self.player_side == "White" and piece.symbol().isupper()) or
                   (self.player_side == "Black" and piece.symbol().islower())):
                    self.selected_square = square
                    self.highlight_square(row, col)
        else:
            # Attempting to make a move
            move_uci = self.selected_square + square
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.player_moves.append(move_uci)
                self.selected_square = None
                self.reset_highlight()
                self.update_board_ui()

                # Show suggestions for player's move
                suggestions = suggest_best_moves(self.board, move_uci)
                self.suggestion_text.delete("1.0", tk.END)
                suggestion_str = f"Instead of {move_uci}, consider:\n"
                for m, explanation in suggestions:
                    suggestion_str += f"{m}: {explanation}\n"
                self.suggestion_text.insert(tk.END, suggestion_str)

                # AI moves next
                self.root.after(500, self.ai_move)
            else:
                messagebox.showerror("Invalid Move", "That move is not legal.")
                self.selected_square = None
                self.reset_highlight()

    def highlight_square(self, row, col):
        """Highlight a selected square in yellow."""
        for r in range(8):
            for c in range(8):
                self.reset_color(r, c)
        self.labels[row+1][col+1].config(bg="yellow")

    def reset_color(self, row, col):
        """Reset a single square's background color."""
        color = "#DDB88C" if (row + col) % 2 == 0 else "#A66D4F"
        self.labels[row+1][col+1].config(bg=color)

    def reset_highlight(self):
        """Reset all squares to their normal color."""
        for row in range(8):
            for col in range(8):
                self.reset_color(row, col)

    def ai_move(self):
        """Have the AI choose a move, push it, and update the board."""
        if self.board.is_game_over():
            result = self.board.result()
            messagebox.showinfo("Game Over", f"Game Over! Result: {result}")
            engine.quit()
            return

        # Until the user has made 3 moves, use balanced style
        if len(self.player_moves) <= 3 and self.ai_style is None:
            time_limit = 0.5
            best_move = get_best_move(self.board, time_limit)
            info_text = f"AI (Balanced) move: {best_move}\nUser moves recorded: {len(self.player_moves)}/3"
            # self.ai_explanation.delete("1.0", tk.END)
            # self.ai_explanation.insert(tk.END, info_text)
        elif self.ai_style is None:
            # Once the user has made 3 moves, determine AI style
            self.ai_style = analyze_player_moves(self.player_moves)
            print(f"AI has chosen {self.ai_style} play style!")  # Print in console (no popup)
            try:
                engine.configure({"WeightsFile": WEIGHTS[self.ai_style]})
            except Exception as e:
                print(f"Error configuring engine weights: {e}")
            time_limit = 0.1 if self.ai_style == "defensive" else 0.5 if self.ai_style == "balanced" else 2.0
            best_move = get_best_move(self.board, time_limit)
            # self.ai_explanation.delete("1.0", tk.END)
            # self.ai_explanation.insert(tk.END, f"AI ({self.ai_style.capitalize()}) move: {best_move}")
        else:
            time_limit = 0.1 if self.ai_style == "defensive" else 0.5 if self.ai_style == "balanced" else 2.0
            best_move = get_best_move(self.board, time_limit)
            # self.ai_explanation.delete("1.0", tk.END)
            # self.ai_explanation.insert(tk.END, f"AI ({self.ai_style.capitalize()}) move: {best_move}")

        # Attempt to apply the AI's move
        move = chess.Move.from_uci(best_move)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.ai_moves.append(best_move)
            self.update_board_ui()
        else:
            messagebox.showerror("Error", f"AI attempted an illegal move: {best_move}")

def run_game():
    root = tk.Tk()
    game = ChessGameGUI(root)
    root.mainloop()
    engine.quit()

if __name__ == "__main__":
    run_game()
