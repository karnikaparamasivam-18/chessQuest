"""Castling, en passant, and promotion behaviour."""

from chess_engine.board import Board
from chess_engine.constants import BLACK, WHITE, name_to_square
from chess_engine.game import Game
from chess_engine.pieces import create_piece
from chess_engine.rules import generate_legal_moves


def _bare_kings_board():
    board = Board(empty=True)
    board.set_piece(name_to_square("e1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("e8"), create_piece("king", BLACK))
    return board


def test_kingside_castling_moves_king_and_rook():
    board = _bare_kings_board()
    board.set_piece(name_to_square("h1"), create_piece("rook", WHITE))

    castle = next(
        m for m in generate_legal_moves(board, WHITE) if m.castle_side == "king"
    )
    board.make_move(castle)

    assert board.piece_at(name_to_square("g1")).piece_type == "king"
    assert board.piece_at(name_to_square("f1")).piece_type == "rook"
    assert board.piece_at(name_to_square("e1")) is None
    assert board.piece_at(name_to_square("h1")) is None


def test_cannot_castle_through_check():
    board = _bare_kings_board()
    board.set_piece(name_to_square("h1"), create_piece("rook", WHITE))
    # A black rook on f8 attacks f1, the square the king would pass through.
    board.set_piece(name_to_square("f8"), create_piece("rook", BLACK))

    assert not any(
        m.castle_side == "king" for m in generate_legal_moves(board, WHITE)
    )


def test_en_passant_capture_removes_the_passed_pawn():
    game = Game()
    game.make_move_from_squares(name_to_square("e2"), name_to_square("e4"))
    game.make_move_from_squares(name_to_square("a7"), name_to_square("a6"))
    game.make_move_from_squares(name_to_square("e4"), name_to_square("e5"))
    # Black double-steps d7-d5 right beside the white e5 pawn.
    game.make_move_from_squares(name_to_square("d7"), name_to_square("d5"))

    assert game.board.en_passant_target == name_to_square("d6")
    game.make_move_from_squares(name_to_square("e5"), name_to_square("d6"))

    assert game.board.piece_at(name_to_square("d6")).piece_type == "pawn"
    assert game.board.piece_at(name_to_square("d5")) is None  # captured pawn gone


def test_pawn_promotes_to_queen_by_default():
    board = Board(empty=True)
    board.set_piece(name_to_square("a7"), create_piece("pawn", WHITE))
    board.set_piece(name_to_square("e1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("h8"), create_piece("king", BLACK))
    game = Game()
    game.board = board
    game.turn = WHITE
    game._legal_cache = None

    game.make_move_from_squares(name_to_square("a7"), name_to_square("a8"))
    assert game.board.piece_at(name_to_square("a8")).piece_type == "queen"


def test_underpromotion_to_knight_is_available():
    board = Board(empty=True)
    board.set_piece(name_to_square("a7"), create_piece("pawn", WHITE))
    board.set_piece(name_to_square("e1"), create_piece("king", WHITE))
    board.set_piece(name_to_square("h8"), create_piece("king", BLACK))
    game = Game()
    game.board = board
    game.turn = WHITE
    game._legal_cache = None

    game.make_move_from_squares(
        name_to_square("a7"), name_to_square("a8"), promotion="knight"
    )
    assert game.board.piece_at(name_to_square("a8")).piece_type == "knight"
