# 2048_game
A simple 2048 game made with Python and Tkinter. You move numbered tiles using arrow keys or WASD to combine them and reach 2048. The game includes Undo, Restart, and Change Size buttons.

 #### What’s in this repo

 Game_2048.py — single-file implementation (pure logic + Tkinter GUI)
 README.md — this file

## Requirements
 Python 3.8+
 
 tkinter (bundled on Windows/macOS; on many Linux distros install python3-tk)

## Run the game
 From the project directory:
 python Game_2048.py
 The window opens with a 4×4 board by default. You can change seed/size inside main() for reproducible demos.

## Gameplay & Controls

Objective: combine tiles with the same number to reach 2048 (you may continue after winning).
After each valid move a new tile appears: 2 (90% chance) or 4 (10% chance).
Game ends when no legal moves remain.
### Controls:
 Arrow keys or W/A/S/D to move tiles. 
 Buttons: 
 Undo — revert the last move (single-step undo stack). 
 Restart — new game with current size/seed. 
 Size... — choose board size (2–8), which rebuilds the UI. 
 #### Notes: 
 Merges occur once per move per tile (proper skip logic implemented).
 Undo restores previous (board, score). 

## Implementation details (concise)
### Separation of concerns
Pure logic (functional style): move/merge/spawn/check functions operate on immutable-style Board objects (Tuple[Tuple[int,...], ...]).
GUI layer (Tkinter): renders board & score and invokes pure functions; all side-effects are here.
### Core functions
move_left(board) -> (new_board, score_gain); move_right, move_up, move_down derived via reverse/transpose.
spawn_random_tile(board, rng) — RNG injected for determinism (random.Random(seed)).
can_move(board), has_won(board) — game state checks.
### Algorithms & complexity
Per-move time: O(N²) — each of N rows processed (compress + merge).
Space: produces a new board per move → O(N²); undo stores previous boards.
### Data structures
Board: tuple-of-tuples for immutability/ease of storing in undo stack.
Undo stack: list of (board, score) snapshots.
