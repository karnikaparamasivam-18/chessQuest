from ..constants import BISHOP
from ..piece import Piece


class Bishop(Piece):
    """Moves any number of squares diagonally."""

    piece_type = BISHOP
    is_sliding = True
    directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
