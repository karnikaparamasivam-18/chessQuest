"""The base :class:`Piece` class shared by every chess piece.

Each concrete piece subclass (in :mod:`chess_engine.pieces`) knows how it moves.
Move generation here is *pseudo-legal*: it obeys the piece's movement pattern
and stops at blockers, but it does not consider whether the moving side's king
would be left in check. Filtering for king safety happens in
:mod:`chess_engine.rules`.
"""

from .constants import PIECE_VALUES, in_bounds
from .move import Move


class Piece:
    """A chess piece of a given colour sitting on the board.

    Subclasses set :attr:`piece_type` and implement :meth:`pseudo_legal_moves`.
    """

    piece_type = None
    is_sliding = False
    # Movement offsets as (delta_row, delta_col) pairs; used by most pieces.
    directions = ()

    def __init__(self, color):
        self.color = color
        # Tracks whether the piece has moved yet -- needed for castling rights
        # and the pawn's initial two-square advance.
        self.has_moved = False

    @property
    def value(self):
        return PIECE_VALUES[self.piece_type]

    def clone(self):
        """Return an independent copy of this piece."""
        copy = type(self)(self.color)
        copy.has_moved = self.has_moved
        return copy

    def _stepping_moves(self, board, from_square):
        """Moves for non-sliding pieces (knight, king): one step per direction."""
        moves = []
        row, col = from_square
        for d_row, d_col in self.directions:
            target = (row + d_row, col + d_col)
            if not in_bounds(*target):
                continue
            occupant = board.piece_at(target)
            if occupant is None:
                moves.append(Move(from_square, target))
            elif occupant.color != self.color:
                moves.append(Move(from_square, target, is_capture=True))
        return moves

    def _sliding_moves(self, board, from_square):
        """Moves for sliding pieces (bishop, rook, queen): rays until blocked."""
        moves = []
        row, col = from_square
        for d_row, d_col in self.directions:
            step = 1
            while True:
                target = (row + d_row * step, col + d_col * step)
                if not in_bounds(*target):
                    break
                occupant = board.piece_at(target)
                if occupant is None:
                    moves.append(Move(from_square, target))
                else:
                    if occupant.color != self.color:
                        moves.append(Move(from_square, target, is_capture=True))
                    break
                step += 1
        return moves

    def pseudo_legal_moves(self, board, from_square):
        """Return pseudo-legal moves for this piece from ``from_square``."""
        if self.is_sliding:
            return self._sliding_moves(board, from_square)
        return self._stepping_moves(board, from_square)

    def __repr__(self):
        return f"{type(self).__name__}({self.color})"
