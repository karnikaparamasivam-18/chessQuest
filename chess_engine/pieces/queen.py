from ..constants import QUEEN
from ..piece import Piece


class Queen(Piece):
    """Combines rook and bishop movement in all eight directions."""

    piece_type = QUEEN
    is_sliding = True
    directions = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    )
