"""REST endpoints for creating and playing games.

These handlers are deliberately synchronous (``def``, not ``async def``) so
FastAPI runs them in its worker thread pool. That keeps a slow Master-level AI
search from blocking the event loop and starving other requests.
"""

from fastapi import APIRouter, HTTPException

from chess_engine.ai import create_ai
from chess_engine.game import IllegalMoveError
from chess_engine.constants import name_to_square

from models.schemas import CreateGameRequest, MoveRequest

from .serializers import serialize_game
from .session import store

router = APIRouter(prefix="/api", tags=["games"])


def _require_game(game_id):
    game = store.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found.")
    return game


def _valid_square(name):
    if len(name) != 2 or name[0] not in "abcdefgh" or name[1] not in "12345678":
        raise HTTPException(status_code=400, detail=f"Invalid square: {name!r}.")
    return name_to_square(name)


@router.post("/games", status_code=201)
def create_game(request: CreateGameRequest):
    if request.mode == "computer" and request.difficulty is None:
        raise HTTPException(
            status_code=400,
            detail="A difficulty is required for computer games.",
        )
    game_id, game = store.create(
        mode=request.mode,
        difficulty=request.difficulty,
        human_color=request.human_color,
    )
    return serialize_game(game, game_id)


@router.get("/games/{game_id}")
def get_game(game_id: str):
    game = _require_game(game_id)
    return serialize_game(game, game_id)


@router.post("/games/{game_id}/moves")
def submit_move(game_id: str, move: MoveRequest):
    game = _require_game(game_id)
    lock = store.lock_for(game_id)
    from_square = _valid_square(move.from_square)
    to_square = _valid_square(move.to_square)
    with lock:
        try:
            game.make_move_from_squares(from_square, to_square, move.promotion)
        except IllegalMoveError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return serialize_game(game, game_id)


@router.post("/games/{game_id}/ai-move")
def ai_move(game_id: str):
    game = _require_game(game_id)
    lock = store.lock_for(game_id)
    with lock:
        if not game.is_ai_turn():
            raise HTTPException(
                status_code=400,
                detail="It is not the computer's turn to move.",
            )
        ai = create_ai(game.ai_difficulty)
        move = ai.choose_move(game)
        if move is None:
            raise HTTPException(status_code=400, detail="No move available.")
        game.push_move(move)
        return serialize_game(game, game_id)


@router.post("/games/{game_id}/undo")
def undo_move(game_id: str):
    game = _require_game(game_id)
    lock = store.lock_for(game_id)
    with lock:
        if game.game_mode != "local":
            raise HTTPException(
                status_code=400,
                detail="Undo is only available in local two-player games.",
            )
        if not game.history:
            raise HTTPException(status_code=400, detail="Nothing to undo.")
        game.undo()
        return serialize_game(game, game_id)


@router.post("/games/{game_id}/restart")
def restart_game(game_id: str):
    game = _require_game(game_id)
    lock = store.lock_for(game_id)
    with lock:
        game.restart()
        return serialize_game(game, game_id)
