from ..constants import (
    BISHOP,
    BLACK,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    in_bounds,
)
from ..move import Move
from ..piece import Piece

# Pieces a pawn may promote to on reaching the far rank.
PROMOTION_CHOICES = (QUEEN, ROOK, BISHOP, KNIGHT)


class Pawn(Piece):
    """Pawns move forward, capture diagonally, and promote on the last rank.

    White pawns travel toward row 0; Black pawns travel toward row 7.
    """

    piece_type = PAWN
    is_sliding = False

    @property
    def _direction(self):
        return -1 if self.color == WHITE else 1

    @property
    def _start_row(self):
        return 6 if self.color == WHITE else 1

    @property
    def _promotion_row(self):
        return 0 if self.color == WHITE else 7

    def _append_forward(self, moves, from_square, target):
        """Add a forward move, expanding into promotions on the last rank."""
        if target[0] == self._promotion_row:
            for choice in PROMOTION_CHOICES:
                moves.append(Move(from_square, target, promotion=choice))
        else:
            moves.append(Move(from_square, target))

    def _append_capture(self, moves, from_square, target, is_en_passant=False):
        if target[0] == self._promotion_row:
            for choice in PROMOTION_CHOICES:
                moves.append(
                    Move(from_square, target, is_capture=True, promotion=choice)
                )
        else:
            moves.append(
                Move(
                    from_square,
                    target,
                    is_capture=True,
                    is_en_passant=is_en_passant,
                )
            )

    def pseudo_legal_moves(self, board, from_square):
        moves = []
        row, col = from_square
        forward = row + self._direction

        # Single forward step onto an empty square.
        if in_bounds(forward, col) and board.piece_at((forward, col)) is None:
            self._append_forward(moves, from_square, (forward, col))

            # Double step from the starting rank, only if both squares are empty.
            double = row + 2 * self._direction
            if row == self._start_row and board.piece_at((double, col)) is None:
                moves.append(
                    Move(from_square, (double, col), is_double_pawn_push=True)
                )

        # Diagonal captures, including en passant.
        for d_col in (-1, 1):
            target = (forward, col + d_col)
            if not in_bounds(*target):
                continue
            occupant = board.piece_at(target)
            if occupant is not None and occupant.color != self.color:
                self._append_capture(moves, from_square, target)
            elif target == board.en_passant_target:
                self._append_capture(moves, from_square, target, is_en_passant=True)

        return moves
