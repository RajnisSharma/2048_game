import tkinter as tk
from tkinter import simpledialog, messagebox
import random
from copy import deepcopy
from typing import List, Tuple

# --------------------
# Pure game logic (pure functions)
# --------------------
Board = Tuple[Tuple[int, ...], ...]  # immutable board type

def empty_board(n: int) -> Board:
    return tuple(tuple(0 for _ in range(n)) for _ in range(n))

def board_to_list(b: Board) -> List[List[int]]:
    return [list(row) for row in b]

def list_to_board(lst: List[List[int]]) -> Board:
    return tuple(tuple(row) for row in lst)

def spawn_random_tile(board: Board, rng: random.Random) -> Board:
    lst = board_to_list(board)
    empties = [(r, c) for r in range(len(lst)) for c in range(len(lst)) if lst[r][c] == 0]
    if not empties:
        return board
    r, c = rng.choice(empties)
    lst[r][c] = 4 if rng.random() < 0.1 else 2
    return list_to_board(lst)

def initialize_board(n: int, rng: random.Random) -> Board:
    b = empty_board(n)
    b = spawn_random_tile(b, rng)
    b = spawn_random_tile(b, rng)
    return b

def transpose(lst: List[List[int]]) -> List[List[int]]:
    n = len(lst)
    return [[lst[r][c] for r in range(n)] for c in range(n)]

def reverse_rows(lst: List[List[int]]) -> List[List[int]]:
    return [list(reversed(row)) for row in lst]

def compress_merge_left_row(row: List[int]) -> Tuple[List[int], int]:
    nonz = [x for x in row if x != 0]
    out = []
    score = 0
    i = 0
    while i < len(nonz):
        if i + 1 < len(nonz) and nonz[i] == nonz[i+1]:
            merged = nonz[i] + nonz[i+1]
            out.append(merged)
            score += merged
            i += 2
        else:
            out.append(nonz[i])
            i += 1
    out += [0] * (len(row) - len(out))
    return out, score

def move_left(board: Board) -> Tuple[Board, int]:
    lst = board_to_list(board)
    n = len(lst)
    moved = False
    total = 0
    new = []
    for r in range(n):
        nr, gained = compress_merge_left_row(lst[r])
        if nr != lst[r]:
            moved = True
        total += gained
        new.append(nr)
    return (list_to_board(new), total) if moved else (board, 0)

def move_right(board: Board) -> Tuple[Board, int]:
    lst = board_to_list(board)
    rev = reverse_rows(lst)
    moved_board, score = move_left(list_to_board(rev))
    if score == 0 and moved_board == list_to_board(rev):
        return board, 0
    return list_to_board(reverse_rows(board_to_list(moved_board))), score

def move_up(board: Board) -> Tuple[Board, int]:
    lst = board_to_list(board)
    t = transpose(lst)
    moved_board, score = move_left(list_to_board(t))
    if score == 0 and moved_board == list_to_board(t):
        return board, 0
    return list_to_board(transpose(board_to_list(moved_board))), score

def move_down(board: Board) -> Tuple[Board, int]:
    lst = board_to_list(board)
    t = transpose(lst)
    moved_board, score = move_right(list_to_board(t))
    if score == 0 and moved_board == list_to_board(t):
        return board, 0
    return list_to_board(transpose(board_to_list(moved_board))), score

def can_move(board: Board) -> bool:
    n = len(board)
    if any(cell == 0 for row in board for cell in row):
        return True
    for r in range(n):
        for c in range(n-1):
            if board[r][c] == board[r][c+1]:
                return True
    for c in range(n):
        for r in range(n-1):
            if board[r][c] == board[r+1][c]:
                return True
    return False

def has_won(board: Board, target=2048) -> bool:
    return any(cell >= target for row in board for cell in row)

# --------------------
# GUI (side-effects)
# --------------------
TILE_BG = {
    0: ("#cdc1b4", "#776e65"),
    2: ("#eee4da", "#776e65"),
    4: ("#ede0c8", "#776e65"),
    8: ("#f2b179", "#f9f6f2"),
    16: ("#f59563", "#f9f6f2"),
    32: ("#f67c5f", "#f9f6f2"),
    64: ("#f65e3b", "#f9f6f2"),
}
class App:
    def __init__(self, root, size=4, seed=None):
        self.root = root
        self.size = max(2, int(size))
        self.rng = random.Random(seed)
        self.best = 0
        self.score = 0
        self.undo_stack = []  # store (board,score)
        self.board = initialize_board(self.size, rng=self.rng)
        self.root.title("2048 - minimal (tkinter)")
        self.build_ui()
        self.update_gui()
        self.root.bind("<Key>", self.on_key)

    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(padx=8, pady=8, anchor="w")
        tk.Label(top, text="Score:").pack(side="left")
        self.score_var = tk.StringVar(value="0")
        tk.Label(top, textvariable=self.score_var, width=6).pack(side="left", padx=6)
        tk.Button(top, text="Undo", command=self.undo).pack(side="right")
        tk.Button(top, text="Restart", command=self.restart).pack(side="right")
        tk.Button(top, text="Size...", command=self.set_size).pack(side="right")

        self.grid_frame = tk.Frame(self.root, bg="#bbada0", padx=8, pady=8)
        self.grid_frame.pack(padx=6, pady=6)
        self.cells = [[None]*self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                lbl = tk.Label(self.grid_frame, text="", width=6, height=3,
                               font=("Helvetica", 20, "bold"), bd=0, relief="flat",
                               bg=TILE_BG[0][0], fg=TILE_BG[0][1])
                lbl.grid(row=r, column=c, padx=6, pady=6)
                self.cells[r][c] = lbl

    def rebuild_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.cells = [[None]*self.size for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                lbl = tk.Label(self.grid_frame, text="", width=6, height=3,
                               font=("Helvetica", 20, "bold"), bd=0, relief="flat",
                               bg=TILE_BG[0][0], fg=TILE_BG[0][1])
                lbl.grid(row=r, column=c, padx=6, pady=6)
                self.cells[r][c] = lbl

    def update_gui(self):
        for r in range(self.size):
            for c in range(self.size):
                val = self.board[r][c]
                bg, fg = TILE_BG.get(val, ("#3c3a32","#f9f6f2"))
                text = "" if val == 0 else str(val)
                self.cells[r][c].config(text=text, bg=bg, fg=fg)
        self.score_var.set(str(self.score))
        self.root.update_idletasks()

    def apply_move(self, move_fn):
        if has_won(self.board) or not can_move(self.board):
            return
        new_board, gained = move_fn(self.board)
        if new_board == self.board:
            return
        # push undo
        self.undo_stack.append((self.board, self.score))
        self.board = spawn_random_tile(new_board, rng=self.rng)
        self.score += gained
        if self.score > self.best:
            self.best = self.score
        self.update_gui()
        if has_won(self.board):
            messagebox.showinfo("You win!", "Reached 2048!")
        elif not can_move(self.board):
            messagebox.showinfo("Game Over", f"Score: {self.score}")

    def on_key(self, e):
        k = e.keysym.lower()
        mapping = {'up': lambda: self.apply_move(move_up),
                   'w': lambda: self.apply_move(move_up),
                   'down': lambda: self.apply_move(move_down),
                   's': lambda: self.apply_move(move_down),
                   'left': lambda: self.apply_move(move_left),
                   'a': lambda: self.apply_move(move_left),
                   'right': lambda: self.apply_move(move_right),
                   'd': lambda: self.apply_move(move_right)}
        if k in mapping:
            mapping[k]()

    def undo(self):
        if not self.undo_stack:
            return
        self.board, self.score = self.undo_stack.pop()
        self.update_gui()

    def restart(self):
        self.score = 0
        self.undo_stack.clear()
        self.board = initialize_board(self.size, rng=self.rng)
        self.update_gui()

    def set_size(self):
        ans = simpledialog.askinteger("Size", "Board size (2-8):", initialvalue=self.size, minvalue=2, maxvalue=8)
        if ans and ans != self.size:
            self.size = int(ans)
            self.rebuild_grid()
            self.restart()

def main():
    root = tk.Tk()
    app = App(root, size=4, seed=42)  # seed optional: deterministic demo
    root.mainloop()

if __name__ == "__main__":
    main()
