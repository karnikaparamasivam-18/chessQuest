"""Beginner: fast, beatable, and only looks one move ahead.

It grabs the most valuable capture on offer, and otherwise plays a random legal
move. No lookahead, so it happily walks into tactics -- which is the point.
"""

from ..rules import generate_legal_moves
from .base import ChessAI


class BeginnerAI(ChessAI):
    difficulty = "beginner"

    def choose_move(self, game):
        board = game.board
        moves = generate_legal_moves(board, game.turn)
        if not moves:
            return None

        captures = [m for m in moves if m.is_capture]
        if captures and self._rng.random() < 0.8:
            # Usually take the best capture; occasionally don't, to stay human.
            return max(captures, key=lambda m: self._capture_value(board, m))

        return self._rng.choice(moves)

    @staticmethod
    def _capture_value(board, move):
        victim = board.piece_at(move.to_square)
        return victim.value if victim else 0
