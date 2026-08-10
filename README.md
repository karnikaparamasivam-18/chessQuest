# ChessQuest — Enchanted Garden Chess

A browser-based chess game with a playful enchanted-garden theme. Play a local
two-player match on the same device, or challenge a computer opponent across
three difficulty levels. The chess engine is written from scratch in Python and
exposed through a small FastAPI backend; the frontend is plain HTML, CSS, and
JavaScript.

## Live Demo

**[Play ChessQuest](https://chessquest.onrender.com)**


## Features

- **Local two-player** on one device, and **Player vs Computer** at three levels.
- **From-scratch chess engine** — full legal-move generation including castling,
  en passant, and promotion, with check, checkmate, stalemate, insufficient-
  material, and fifty-move draw detection.
- **Three AI opponents**
  - *Beginner* — fast one-ply, capture-seeking play.
  - *Thinker* — depth-limited Minimax.
  - *Master* — deeper Minimax with Alpha-Beta pruning, move ordering, and
    piece-square-table evaluation.
- **Polished garden UI** — legal-move highlighting, move animation, check and
  last-move indicators, move history, captured pieces, and subtle synthesised
  sound effects with a mute toggle.

## Tech stack

- **Backend:** Python 3, FastAPI, Pydantic
- **Engine & AI:** pure Python (2D board, OOP piece hierarchy, Minimax +
  Alpha-Beta), no external chess library for the core rules
- **Frontend:** HTML5, CSS3, vanilla JavaScript (ES modules)
- **Testing:** pytest (engine, AI, and API), verified with perft node counts

## Getting started

Requires Python 3.10+.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
uvicorn app.main:app --reload
```

Then open <http://localhost:8000> and play.

## Running the tests

```bash
pytest
```

The suite covers piece movement, special moves, check/checkmate/stalemate,
draws, undo, all three AI levels, and the API endpoints. Move generation is
anchored by perft counts from the initial position (20 / 400 / 8902 / 197281).

## Project structure

```
app/            FastAPI application entry point
api/            REST routes, request/response serialization, in-memory store
models/         Pydantic request models
chess_engine/   Board, pieces, rules, move, game state
  pieces/       King, Queen, Rook, Bishop, Knight, Pawn
  ai/           Beginner, Thinker, Master, shared search core
  evaluation.py Board evaluation (material + piece-square tables)
frontend/       HTML, CSS, JavaScript, game UI
tests/          pytest suite
```

The engine has no dependency on FastAPI or the frontend, so it can be imported
and tested on its own.

## API overview

| Method | Endpoint                         | Purpose                         |
| ------ | -------------------------------- | ------------------------------- |
| POST   | `/api/games`                     | Create a new game               |
| GET    | `/api/games/{id}`                | Get current game state          |
| POST   | `/api/games/{id}/moves`          | Submit a move                   |
| POST   | `/api/games/{id}/ai-move`        | Request the computer's move     |
| POST   | `/api/games/{id}/undo`           | Undo (local two-player only)    |
| POST   | `/api/games/{id}/restart`        | Restart the game                |

## Deployment

The app serves its own frontend, so a single web service is all that's needed.
See `render.yaml` for a ready-to-use configuration; the start command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Games are held in memory, so a single always-on instance is the intended setup.
