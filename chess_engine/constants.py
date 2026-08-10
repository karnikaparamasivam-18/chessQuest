"""Shared constants and small coordinate helpers used across the engine.

Board coordinates use (row, col) with row 0 at the top of the board:

    row 0  -> rank 8  (Black's back rank)
    row 7  -> rank 1  (White's back rank)
    col 0  -> file 'a'
    col 7  -> file 'h'

So the human-readable square name for (row, col) is
``file_letter + rank_number`` -- e.g. (6, 4) is "e2".
"""

BOARD_SIZE = 8

WHITE = "white"
BLACK = "black"

# Piece type identifiers.
KING = "king"
QUEEN = "queen"
ROOK = "rook"
BISHOP = "bishop"
KNIGHT = "knight"
PAWN = "pawn"

# Material values used by the evaluation function and simple AI heuristics.
PIECE_VALUES = {
    PAWN: 1,
    KNIGHT: 3,
    BISHOP: 3,
    ROOK: 5,
    QUEEN: 9,
    KING: 1000,
}


def opponent(color):
    """Return the colour that opposes ``color``."""
    return BLACK if color == WHITE else WHITE


def in_bounds(row, col):
    """True if (row, col) sits on the 8x8 board."""
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def square_to_name(square):
    """Convert a (row, col) tuple to a square name such as "e2"."""
    row, col = square
    file_letter = chr(ord("a") + col)
    rank_number = BOARD_SIZE - row
    return f"{file_letter}{rank_number}"


def name_to_square(name):
    """Convert a square name such as "e2" to a (row, col) tuple."""
    file_letter, rank_number = name[0], name[1]
    col = ord(file_letter) - ord("a")
    row = BOARD_SIZE - int(rank_number)
    return (row, col)
