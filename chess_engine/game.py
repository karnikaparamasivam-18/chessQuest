"""High-level game state: turns, move history, undo, and terminal detection.

:class:`Game` wraps a :class:`~chess_engine.board.Board` and is the object the
API layer talks to. It validates that a requested move is legal, applies it,
switches turns, and recomputes the game status (check / checkmate / stalemate /
draw). It also serialises itself to plain data for the frontend.
"""

from .board import Board
from .constants import (
    BISHOP,
    BLACK,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    opponent,
    square_to_name,
)
from .rules import generate_legal_moves, has_any_legal_move, is_in_check

# Game status values.
ONGOING = "ongoing"
CHECK = "check"
CHECKMATE = "checkmate"
STALEMATE = "stalemate"
DRAW_FIFTY = "draw_fifty_move"
DRAW_INSUFFICIENT = "draw_insufficient_material"

_TERMINAL_STATUSES = {CHECKMATE, STALEMATE, DRAW_FIFTY, DRAW_INSUFFICIENT}


class IllegalMoveError(Exception):
    """Raised when a requested move is not legal in the current position."""


class Game:
    """A single chess game and its full history."""

    def __init__(self, game_mode="local", ai_difficulty=None, human_color=WHITE):
        self.board = Board()
        self.turn = WHITE
        self.game_mode = game_mode
        self.ai_difficulty = ai_difficulty
        # In computer mode the human plays one colour and the AI the other.
        self.human_color = human_color
        self.ai_color = opponent(human_color) if game_mode == "computer" else None
        self.status = ONGOING
        self.winner = None
        # Stack of (move, undo_record) so moves can be reversed in order.
        self.history = []
        # Pieces removed from play, in capture order.
        self.captured_pieces = []
        self._legal_cache = None

    # ---------------------------------------------------------- legal moves
    def legal_moves(self):
        """Legal moves for the side to move (cached until the position changes)."""
        if self._legal_cache is None:
            self._legal_cache = generate_legal_moves(self.board, self.turn)
        return self._legal_cache

    def find_legal_move(self, from_square, to_square, promotion=None):
        """Return the legal move matching the request, or None if there isn't one.

        Promotion defaults to a queen when the client omits it, matching the
        auto-queen behaviour of the current UI.
        """
        from_square = tuple(from_square)
        to_square = tuple(to_square)
        matches = [
            m
            for m in self.legal_moves()
            if m.from_square == from_square and m.to_square == to_square
        ]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        # Multiple matches means a promotion choice; pick the requested piece
        # or default to a queen.
        wanted = promotion or QUEEN
        for move in matches:
            if move.promotion == wanted:
                return move
        return matches[0]

    # --------------------------------------------------------------- moving
    def push_move(self, move):
        """Apply an already-legal move and advance the game state."""
        if self.is_over():
            raise IllegalMoveError("The game is already over.")
        undo = self.board.make_move(move)
        if undo.captured_piece is not None:
            self.captured_pieces.append(undo.captured_piece)
        self.history.append((move, undo))
        self.turn = opponent(self.turn)
        self._legal_cache = None
        self._update_status()
        return move

    def make_move_from_squares(self, from_square, to_square, promotion=None):
        """Validate a requested move by squares and apply it if legal."""
        move = self.find_legal_move(from_square, to_square, promotion)
        if move is None:
            raise IllegalMoveError(
                f"Illegal move: {square_to_name(tuple(from_square))} to "
                f"{square_to_name(tuple(to_square))}."
            )
        return self.push_move(move)

    def undo(self):
        """Reverse the most recent move. Returns the move, or None if empty."""
        if not self.history:
            return None
        move, undo = self.history.pop()
        if undo.captured_piece is not None and self.captured_pieces:
            self.captured_pieces.pop()
        self.board.unmake_move(undo)
        self.turn = opponent(self.turn)
        self.winner = None
        self._legal_cache = None
        self._update_status()
        return move

    def restart(self):
        """Reset to the initial position, keeping mode and difficulty."""
        mode, difficulty, human = self.game_mode, self.ai_difficulty, self.human_color
        self.__init__(game_mode=mode, ai_difficulty=difficulty, human_color=human)

    def is_ai_turn(self):
        """True if it is the computer opponent's turn to move."""
        return (
            self.game_mode == "computer"
            and not self.is_over()
            and self.turn == self.ai_color
        )

    # ---------------------------------------------------------- status logic
    def is_over(self):
        return self.status in _TERMINAL_STATUSES

    def _update_status(self):
        if self._is_insufficient_material():
            self.status = DRAW_INSUFFICIENT
            self.winner = None
            return

        if not has_any_legal_move(self.board, self.turn):
            if is_in_check(self.board, self.turn):
                self.status = CHECKMATE
                self.winner = opponent(self.turn)
            else:
                self.status = STALEMATE
                self.winner = None
            return

        # Fifty-move rule: 100 half-moves without a pawn move or capture.
        if self.board.halfmove_clock >= 100:
            self.status = DRAW_FIFTY
            self.winner = None
            return

        if is_in_check(self.board, self.turn):
            self.status = CHECK
        else:
            self.status = ONGOING

    def _is_insufficient_material(self):
        """Detect the common draws where neither side can force mate."""
        minors = {WHITE: [], BLACK: []}
        for square, piece in self.board.iter_pieces():
            ptype = piece.piece_type
            if ptype in (PAWN, ROOK, QUEEN):
                return False  # Mating material still exists.
            if ptype in (BISHOP, KNIGHT):
                minors[piece.color].append((ptype, square))

        white_minors = minors[WHITE]
        black_minors = minors[BLACK]

        # King vs King.
        if not white_minors and not black_minors:
            return True
        # King + single minor vs King.
        if len(white_minors) + len(black_minors) == 1:
            return True
        # King + Bishop vs King + Bishop with both bishops on the same colour.
        if (
            len(white_minors) == 1
            and len(black_minors) == 1
            and white_minors[0][0] == BISHOP
            and black_minors[0][0] == BISHOP
        ):
            w_sq = white_minors[0][1]
            b_sq = black_minors[0][1]
            if (w_sq[0] + w_sq[1]) % 2 == (b_sq[0] + b_sq[1]) % 2:
                return True

        return False
