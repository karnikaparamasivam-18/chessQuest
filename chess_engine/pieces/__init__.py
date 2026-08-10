"""Concrete chess piece classes and a small factory helper."""

from ..constants import BISHOP, KING, KNIGHT, PAWN, QUEEN, ROOK
from .bishop import Bishop
from .king import King
from .knight import Knight
from .pawn import Pawn
from .queen import Queen
from .rook import Rook

_PIECE_CLASSES = {
    KING: King,
    QUEEN: Queen,
    ROOK: Rook,
    BISHOP: Bishop,
    KNIGHT: Knight,
    PAWN: Pawn,
}


def create_piece(piece_type, color):
    """Build a piece instance from its type identifier and colour."""
    return _PIECE_CLASSES[piece_type](color)


__all__ = [
    "Bishop",
    "King",
    "Knight",
    "Pawn",
    "Queen",
    "Rook",
    "create_piece",
]
