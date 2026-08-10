"""Small helpers shared across the test suite."""

from chess_engine.board import Board
from chess_engine.constants import opponent
from chess_engine.pieces import create_piece
from chess_engine.rules import generate_legal_moves


def empty_board():
    return Board(empty=True)


def place(board, name_to_square, square_name, piece_type, color):
    """Place a piece by square name (e.g. "e1") on the board."""
    board.set_piece(name_to_square(square_name), create_piece(piece_type, color))


def perft(board, color, depth):
    """Count leaf nodes of the legal-move tree to ``depth`` (move-gen check)."""
    if depth == 0:
        return 1
    total = 0
    for move in generate_legal_moves(board, color):
        undo = board.make_move(move)
        total += perft(board, opponent(color), depth - 1)
        board.unmake_move(undo)
    return total
