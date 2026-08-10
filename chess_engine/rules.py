"""Legal-move generation and check/terminal-state detection.

Pieces produce *pseudo-legal* moves; this module adds castling and then filters
out any move that would leave the mover's own king in check, yielding the set
of fully legal moves. Checkmate and stalemate fall out of "in check?" plus
"any legal move?".
"""

from .constants import KING, ROOK, WHITE, opponent


def _has_rook(board, square, color):
    piece = board.piece_at(square)
    return piece is not None and piece.piece_type == ROOK and piece.color == color


def is_in_check(board, color):
    """True if ``color``'s king is currently attacked."""
    king_square = board.find_king(color)
    if king_square is None:
        return False
    return board.is_square_attacked(king_square, opponent(color))


def generate_legal_moves(board, color):
    """Return every fully legal move for ``color`` in the current position."""
    legal = []
    for square, piece in list(board.iter_pieces(color)):
        candidates = piece.pseudo_legal_moves(board, square)
        if piece.piece_type == KING:
            candidates = candidates + _castling_moves(board, color, square)
        for move in candidates:
            if _leaves_king_safe(board, color, move):
                legal.append(move)
    return legal


def _leaves_king_safe(board, color, move):
    """Play ``move``, test the king, then roll back."""
    undo = board.make_move(move)
    king_square = board.find_king(color)
    safe = not board.is_square_attacked(king_square, opponent(color))
    board.unmake_move(undo)
    return safe


def _castling_moves(board, color, king_square):
    """Generate any legal castling moves for ``color``'s king."""
    from .move import Move  # local import to avoid a cycle at module load

    moves = []
    home_row = 7 if color == WHITE else 0

    # The king must be on its home square and not currently in check.
    if king_square != (home_row, 4):
        return moves
    if board.is_square_attacked(king_square, opponent(color)):
        return moves

    enemy = opponent(color)

    # King-side: squares f, g must be empty; king travels e -> f -> g unattacked.
    if board.castling_rights.get((color, "king")) and _has_rook(
        board, (home_row, 7), color
    ):
        if (
            board.piece_at((home_row, 5)) is None
            and board.piece_at((home_row, 6)) is None
            and not board.is_square_attacked((home_row, 5), enemy)
            and not board.is_square_attacked((home_row, 6), enemy)
        ):
            moves.append(
                Move((home_row, 4), (home_row, 6), castle_side="king")
            )

    # Queen-side: b, c, d empty; king travels e -> d -> c unattacked.
    if board.castling_rights.get((color, "queen")) and _has_rook(
        board, (home_row, 0), color
    ):
        if (
            board.piece_at((home_row, 1)) is None
            and board.piece_at((home_row, 2)) is None
            and board.piece_at((home_row, 3)) is None
            and not board.is_square_attacked((home_row, 3), enemy)
            and not board.is_square_attacked((home_row, 2), enemy)
        ):
            moves.append(
                Move((home_row, 4), (home_row, 2), castle_side="queen")
            )

    return moves


def has_any_legal_move(board, color):
    """True if ``color`` has at least one legal move (used for mate/stalemate)."""
    for square, piece in list(board.iter_pieces(color)):
        candidates = piece.pseudo_legal_moves(board, square)
        if piece.piece_type == KING:
            candidates = candidates + _castling_moves(board, color, square)
        for move in candidates:
            if _leaves_king_safe(board, color, move):
                return True
    return False
