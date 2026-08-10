"""Behaviour and legality checks for the three computer opponents."""

import pytest

from chess_engine.ai import BEGINNER, MASTER, THINKER, create_ai
from chess_engine.board import Board
from chess_engine.constants import BLACK, WHITE, name_to_square
from chess_engine.game import CHECKMATE, Game
from chess_engine.pieces import create_piece
from chess_engine.rules import generate_legal_moves


def _is_legal(game, move):
    return any(
        m.from_square == move.from_square
        and m.to_square == move.to_square
        and m.promotion == move.promotion
        for m in generate_legal_moves(game.board, game.turn)
    )


@pytest.mark.parametrize("difficulty", [BEGINNER, THINKER, MASTER])
def test_ai_returns_a_legal_opening_move(difficulty):
    game = Game(game_mode="computer", ai_difficulty=difficulty)
    ai = create_ai(difficulty, seed=1)
    move = ai.choose_move(game)
    assert move is not None
    assert _is_legal(game, move)


@pytest.mark.parametrize("difficulty", [BEGINNER, THINKER, MASTER])
def test_ai_returns_none_when_no_moves(difficulty):
    # Fool's mate leaves White with no reply.
    game = Game()
    for frm, to in [("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")]:
        game.make_move_from_squares(name_to_square(frm), name_to_square(to))
    assert game.status == CHECKMATE
    ai = create_ai(difficulty, seed=1)
    assert ai.choose_move(game) is None


def test_beginner_takes_a_free_piece():
    board = Board(empty=True)
    board.set_piece(name_to_square("e1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("e8"), create_piece("king", BLACK))
    board.set_piece(name_to_square("a1"), create_piece("rook", WHITE))
    board.set_piece(name_to_square("a7"), create_piece("queen", BLACK))
    game = Game()
    game.board = board
    game.turn = WHITE
    game._legal_cache = None
    game._update_status()

    move = create_ai(BEGINNER, seed=1).choose_move(game)
    assert move.to_square == name_to_square("a7")  # capture the queen


def test_master_finds_mate_in_one():
    # Back-rank mate: Ra1-a8 is checkmate.
    board = Board(empty=True)
    board.set_piece(name_to_square("g1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("a1"), create_piece("rook", WHITE))
    board.set_piece(name_to_square("g8"), create_piece("king", BLACK))
    board.set_piece(name_to_square("f7"), create_piece("pawn", BLACK))
    board.set_piece(name_to_square("g7"), create_piece("pawn", BLACK))
    board.set_piece(name_to_square("h7"), create_piece("pawn", BLACK))
    game = Game()
    game.board = board
    game.turn = WHITE
    game._legal_cache = None
    game._update_status()

    move = create_ai(MASTER, seed=1).choose_move(game)
    game.push_move(move)
    assert move.to_square == name_to_square("a8")
    assert game.status == CHECKMATE
    assert game.winner == WHITE
