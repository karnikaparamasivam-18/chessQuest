"""Check, checkmate, stalemate, draws, and undo."""

from chess_engine.board import Board
from chess_engine.constants import BLACK, WHITE, name_to_square
from chess_engine.game import (
    CHECKMATE,
    DRAW_INSUFFICIENT,
    ONGOING,
    STALEMATE,
    Game,
)
from chess_engine.pieces import create_piece


def _game_from_pieces(pieces, turn=WHITE):
    """Build a Game from a list of (square_name, type, color)."""
    board = Board(empty=True)
    for square_name, ptype, color in pieces:
        board.set_piece(name_to_square(square_name), create_piece(ptype, color))
    game = Game()
    game.board = board
    game.turn = turn
    game._legal_cache = None
    game._update_status()
    return game


def test_fools_mate_is_detected_as_checkmate():
    game = Game()
    game.make_move_from_squares(name_to_square("f2"), name_to_square("f3"))
    game.make_move_from_squares(name_to_square("e7"), name_to_square("e5"))
    game.make_move_from_squares(name_to_square("g2"), name_to_square("g4"))
    game.make_move_from_squares(name_to_square("d8"), name_to_square("h4"))

    assert game.status == CHECKMATE
    assert game.winner == BLACK
    assert game.is_over()


def test_stalemate_king_in_corner():
    game = _game_from_pieces(
        [
            ("h8", "king", BLACK),
            ("f7", "king", WHITE),
            ("g6", "queen", WHITE),
        ],
        turn=BLACK,
    )
    assert game.status == STALEMATE
    assert game.winner is None
    assert game.is_over()


def test_king_vs_king_is_insufficient_material():
    game = _game_from_pieces(
        [("e1", "king", WHITE), ("e8", "king", BLACK)],
    )
    assert game.status == DRAW_INSUFFICIENT


def test_king_and_knight_vs_king_is_insufficient_material():
    game = _game_from_pieces(
        [
            ("e1", "king", WHITE),
            ("g1", "knight", WHITE),
            ("e8", "king", BLACK),
        ],
    )
    assert game.status == DRAW_INSUFFICIENT


def test_undo_restores_exact_position():
    game = Game()
    game.make_move_from_squares(name_to_square("e2"), name_to_square("e4"))
    game.make_move_from_squares(name_to_square("c7"), name_to_square("c5"))

    legal_before = len(game.legal_moves())
    game.make_move_from_squares(name_to_square("g1"), name_to_square("f3"))
    game.undo()

    assert game.turn == WHITE
    assert len(game.legal_moves()) == legal_before
    assert game.board.piece_at(name_to_square("f3")) is None
    assert game.board.piece_at(name_to_square("g1")).piece_type == "knight"


def test_new_game_starts_ongoing_with_white_to_move():
    game = Game()
    assert game.status == ONGOING
    assert game.turn == WHITE
    assert len(game.history) == 0
