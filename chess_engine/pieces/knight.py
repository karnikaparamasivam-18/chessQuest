from ..constants import KNIGHT
from ..piece import Piece


class Knight(Piece):
    """Jumps in an L-shape; not blocked by intervening pieces."""

    piece_type = KNIGHT
    is_sliding = False
    directions = (
        (-2, -1),
        (-2, 1),
        (-1, -2),
        (-1, 2),
        (1, -2),
        (1, 2),
        (2, -1),
        (2, 1),
    )
