"""The board: piece placement, applying/reversing moves, and attack queries.

The board owns the authoritative position. It knows how to *make* and *unmake*
a fully-formed :class:`~chess_engine.move.Move` (so AI search can explore and
roll back cheaply) and how to answer "is this square attacked?", which check
detection and castling both rely on.
"""

from .constants import (
    BISHOP,
    BLACK,
    BOARD_SIZE,
    KING,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    in_bounds,
)
from .move import UndoRecord
from .pieces import create_piece

_KNIGHT_OFFSETS = (
    (-2, -1), (-2, 1), (-1, -2), (-1, 2),
    (1, -2), (1, 2), (2, -1), (2, 1),
)
_KING_OFFSETS = (
    (-1, -1), (-1, 0), (-1, 1), (0, -1),
    (0, 1), (1, -1), (1, 0), (1, 1),
)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))

# Starting arrangement of the back rank, file a -> h.
_BACK_RANK = (ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK)

# Home squares used to maintain castling rights.
_ROOK_HOME = {
    (WHITE, "king"): (7, 7),
    (WHITE, "queen"): (7, 0),
    (BLACK, "king"): (0, 7),
    (BLACK, "queen"): (0, 0),
}


class Board:
    """An 8x8 chess board plus the position state that moves depend on."""

    def __init__(self, empty=False):
        self.squares = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.en_passant_target = None
        self.castling_rights = {
            (WHITE, "king"): True,
            (WHITE, "queen"): True,
            (BLACK, "king"): True,
            (BLACK, "queen"): True,
        }
        # Moves since the last capture or pawn move (for the fifty-move rule).
        self.halfmove_clock = 0
        if not empty:
            self._setup_starting_position()

    # ------------------------------------------------------------------ setup
    def _setup_starting_position(self):
        for col, piece_type in enumerate(_BACK_RANK):
            self.squares[0][col] = create_piece(piece_type, BLACK)
            self.squares[1][col] = create_piece(PAWN, BLACK)
            self.squares[6][col] = create_piece(PAWN, WHITE)
            self.squares[7][col] = create_piece(piece_type, WHITE)

    # ------------------------------------------------------------ basic access
    def piece_at(self, square):
        row, col = square
        return self.squares[row][col]

    def set_piece(self, square, piece):
        row, col = square
        self.squares[row][col] = piece

    def iter_pieces(self, color=None):
        """Yield (square, piece) for every piece, optionally filtered by colour."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.squares[row][col]
                if piece is not None and (color is None or piece.color == color):
                    yield (row, col), piece

    def find_king(self, color):
        for square, piece in self.iter_pieces(color):
            if piece.piece_type == KING:
                return square
        return None

    # --------------------------------------------------------- attack queries
    def is_square_attacked(self, square, by_color):
        """True if any ``by_color`` piece attacks ``square``."""
        row, col = square

        # Pawn attacks: an enemy pawn sits one rank "behind" the target.
        pawn_move_dir = -1 if by_color == WHITE else 1
        attacker_row = row - pawn_move_dir
        for d_col in (-1, 1):
            target = (attacker_row, col + d_col)
            if in_bounds(*target):
                piece = self.piece_at(target)
                if piece and piece.color == by_color and piece.piece_type == PAWN:
                    return True

        # Knight attacks.
        for d_row, d_col in _KNIGHT_OFFSETS:
            target = (row + d_row, col + d_col)
            if in_bounds(*target):
                piece = self.piece_at(target)
                if piece and piece.color == by_color and piece.piece_type == KNIGHT:
                    return True

        # Adjacent king.
        for d_row, d_col in _KING_OFFSETS:
            target = (row + d_row, col + d_col)
            if in_bounds(*target):
                piece = self.piece_at(target)
                if piece and piece.color == by_color and piece.piece_type == KING:
                    return True

        # Sliding attacks along ranks/files (rook, queen).
        if self._ray_hits(square, _ORTHOGONAL, by_color, (ROOK, QUEEN)):
            return True
        # Sliding attacks along diagonals (bishop, queen).
        if self._ray_hits(square, _DIAGONAL, by_color, (BISHOP, QUEEN)):
            return True

        return False

    def _ray_hits(self, square, directions, by_color, piece_types):
        row, col = square
        for d_row, d_col in directions:
            step = 1
            while True:
                target = (row + d_row * step, col + d_col * step)
                if not in_bounds(*target):
                    break
                piece = self.piece_at(target)
                if piece is not None:
                    if piece.color == by_color and piece.piece_type in piece_types:
                        return True
                    break
                step += 1
        return False

    # -------------------------------------------------------- make / unmake
    def make_move(self, move):
        """Apply ``move`` and return an :class:`UndoRecord` to reverse it."""
        piece = self.piece_at(move.from_square)
        undo = UndoRecord(
            move=move,
            prev_en_passant_target=self.en_passant_target,
            prev_castling_rights=dict(self.castling_rights),
            prev_halfmove_clock=self.halfmove_clock,
            moved_piece_first_move=piece.has_moved,
        )

        # Determine and remove any captured piece.
        if move.is_en_passant:
            captured_square = (move.from_square[0], move.to_square[1])
        else:
            captured_square = move.to_square
        captured = self.piece_at(captured_square)
        if captured is not None:
            undo.captured_piece = captured
            undo.captured_square = captured_square
            self.set_piece(captured_square, None)

        # Move the piece.
        self.set_piece(move.from_square, None)
        if move.promotion:
            piece = create_piece(move.promotion, piece.color)
        piece.has_moved = True
        self.set_piece(move.to_square, piece)

        # Move the rook when castling.
        if move.castle_side:
            undo.rook_move = self._move_castling_rook(piece.color, move.castle_side)

        # Update en-passant target (only set behind a double pawn push).
        if move.is_double_pawn_push:
            middle_row = (move.from_square[0] + move.to_square[0]) // 2
            self.en_passant_target = (middle_row, move.from_square[1])
        else:
            self.en_passant_target = None

        self._update_castling_rights(move, piece.color, captured, captured_square)

        # Fifty-move clock: reset on pawn move or capture, otherwise advance.
        if piece.piece_type == PAWN or captured is not None:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        return undo

    def unmake_move(self, undo):
        move = undo.move
        piece = self.piece_at(move.to_square)

        # Restore a promoted pawn to a pawn.
        if move.promotion:
            piece = create_piece(PAWN, piece.color)
        piece.has_moved = undo.moved_piece_first_move

        self.set_piece(move.to_square, None)
        self.set_piece(move.from_square, piece)

        # Restore any captured piece on its original square.
        if undo.captured_piece is not None:
            self.set_piece(undo.captured_square, undo.captured_piece)

        # Put the castling rook back.
        if undo.rook_move is not None:
            rook_from, rook_to = undo.rook_move
            rook = self.piece_at(rook_to)
            self.set_piece(rook_to, None)
            self.set_piece(rook_from, rook)
            rook.has_moved = False

        self.en_passant_target = undo.prev_en_passant_target
        self.castling_rights = undo.prev_castling_rights
        self.halfmove_clock = undo.prev_halfmove_clock

    def _move_castling_rook(self, color, side):
        home_row = 7 if color == WHITE else 0
        if side == "king":
            rook_from = (home_row, 7)
            rook_to = (home_row, 5)
        else:
            rook_from = (home_row, 0)
            rook_to = (home_row, 3)
        rook = self.piece_at(rook_from)
        self.set_piece(rook_from, None)
        rook.has_moved = True
        self.set_piece(rook_to, rook)
        return (rook_from, rook_to)

    def _update_castling_rights(self, move, color, captured, captured_square):
        piece = self.piece_at(move.to_square)

        # Any king move forfeits both castling rights for that colour.
        if piece.piece_type == KING:
            self.castling_rights[(color, "king")] = False
            self.castling_rights[(color, "queen")] = False

        # A rook leaving its home square forfeits that side.
        for key, home in _ROOK_HOME.items():
            if move.from_square == home:
                self.castling_rights[key] = False
            # A rook captured on its home square forfeits the owner's right.
            if captured is not None and captured_square == home:
                self.castling_rights[key] = False

    # ------------------------------------------------------------------ copy
    def clone(self):
        copy = Board(empty=True)
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.squares[row][col]
                copy.squares[row][col] = piece.clone() if piece else None
        copy.en_passant_target = self.en_passant_target
        copy.castling_rights = dict(self.castling_rights)
        copy.halfmove_clock = self.halfmove_clock
        return copy
