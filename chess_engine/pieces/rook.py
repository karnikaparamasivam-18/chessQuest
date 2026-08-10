from ..constants import ROOK
from ..piece import Piece


class Rook(Piece):
    """Moves any number of squares horizontally or vertically."""

    piece_type = ROOK
    is_sliding = True
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
