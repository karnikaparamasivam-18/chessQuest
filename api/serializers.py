"""Convert engine objects into plain dictionaries for JSON responses.

The frontend receives a single self-describing game-state object: the board
grid, whose turn it is, the game status, the legal moves it can highlight, the
captured pieces, and the move history in coordinate notation.
"""

from chess_engine.constants import BOARD_SIZE, square_to_name


def serialize_move(move):
    """A single move as {from, to, promotion, flags} using square names."""
    return {
        "from": square_to_name(move.from_square),
        "to": square_to_name(move.to_square),
        "promotion": move.promotion,
        "is_capture": move.is_capture,
        "is_en_passant": move.is_en_passant,
        "castle_side": move.castle_side,
    }


def _notation(move):
    """Coordinate-style notation such as "e2->e4" or "e5xd6", plus promotion."""
    separator = "x" if move.is_capture else "-"
    text = f"{square_to_name(move.from_square)}{separator}{square_to_name(move.to_square)}"
    if move.promotion:
        text += f"={move.promotion[0].upper()}"
    return text


def serialize_board(board):
    """The 8x8 grid, row 0 = rank 8, each cell null or {type, color}."""
    grid = []
    for row in range(BOARD_SIZE):
        cells = []
        for col in range(BOARD_SIZE):
            piece = board.squares[row][col]
            if piece is None:
                cells.append(None)
            else:
                cells.append({"type": piece.piece_type, "color": piece.color})
        grid.append(cells)
    return grid


def serialize_game(game, game_id):
    """The full game-state payload the frontend renders from."""
    last_move = game.history[-1][0] if game.history else None

    captured = {"white": [], "black": []}
    for piece in game.captured_pieces:
        captured[piece.color].append(piece.piece_type)

    move_history = [
        {**serialize_move(move), "notation": _notation(move)}
        for move, _ in game.history
    ]

    return {
        "game_id": game_id,
        "game_mode": game.game_mode,
        "ai_difficulty": game.ai_difficulty,
        "human_color": game.human_color,
        "ai_color": game.ai_color,
        "turn": game.turn,
        "status": game.status,
        "winner": game.winner,
        "is_over": game.is_over(),
        "in_check": game.status == "check"
        or (game.status == "checkmate"),
        "board": serialize_board(game.board),
        "legal_moves": [serialize_move(m) for m in game.legal_moves()],
        "captured": captured,
        "move_history": move_history,
        "last_move": serialize_move(last_move) if last_move else None,
        "is_ai_turn": game.is_ai_turn(),
        # Undo is available only in local two-player mode (see product spec).
        "can_undo": game.game_mode == "local" and len(game.history) > 0,
    }
