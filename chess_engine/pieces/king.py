from ..constants import KING
from ..piece import Piece


class King(Piece):
    """Moves one square in any direction.

    Castling is not produced here because it depends on whole-board check
    information; it is generated in :mod:`chess_engine.rules`.
    """

    piece_type = KING
    is_sliding = False
    directions = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )
