"""Move-generation correctness, anchored by perft node counts."""

import pytest

from chess_engine.board import Board
from chess_engine.constants import WHITE, name_to_square
from chess_engine.rules import generate_legal_moves

from .helpers import perft


def test_initial_position_has_twenty_moves():
    board = Board()
    assert len(generate_legal_moves(board, WHITE)) == 20


@pytest.mark.parametrize(
    "depth, expected",
    [(1, 20), (2, 400), (3, 8902), (4, 197281)],
)
def test_perft_from_initial_position(depth, expected):
    """The initial-position perft numbers are a well-known reference set."""
    board = Board()
    assert perft(board, WHITE, depth) == expected


def test_knight_moves_from_center_on_empty_board():
    board = Board(empty=True)
    from chess_engine.pieces import create_piece

    board.set_piece(name_to_square("d4"), create_piece("knight", WHITE))
    board.set_piece(name_to_square("e1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("e8"), create_piece("king", "black"))
    knight_moves = [
        m
        for m in generate_legal_moves(board, WHITE)
        if m.from_square == name_to_square("d4")
    ]
    assert len(knight_moves) == 8
