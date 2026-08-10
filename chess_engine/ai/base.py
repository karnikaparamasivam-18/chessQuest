"""Common interface and shared search core for the computer opponents.

``Thinker`` and ``Master`` both search with the same negamax routine; they
differ only in depth, whether alpha-beta pruning is on, move ordering, and the
evaluation function. Keeping the search in one place makes those differences
explicit and easy to reason about.
"""

import random

from ..constants import opponent
from ..evaluation import evaluate
from ..rules import generate_legal_moves, is_in_check

# A score large enough to represent checkmate; offset by ply so the search
# prefers mating sooner and avoiding mate longer.
MATE_SCORE = 1_000_000


class ChessAI:
    """Base class for every computer opponent.

    Subclasses implement :meth:`choose_move`, which returns a legal
    :class:`~chess_engine.move.Move` for the side to move, or ``None`` if there
    is no move (the game is already over).
    """

    difficulty = None

    def __init__(self, seed=None):
        # A private RNG keeps AI behaviour reproducible in tests without
        # touching global random state.
        self._rng = random.Random(seed)

    def choose_move(self, game):  # pragma: no cover - abstract
        raise NotImplementedError


class SearchingAI(ChessAI):
    """An AI that picks its move with a depth-limited negamax search."""

    depth = 2
    use_alpha_beta = False
    order_moves = False
    use_placement = False

    def choose_move(self, game):
        board = game.board
        color = game.turn
        moves = generate_legal_moves(board, color)
        if not moves:
            return None

        if self.order_moves:
            moves = self._ordered(board, moves)

        best_moves = []
        best_score = -MATE_SCORE - 1
        alpha, beta = -MATE_SCORE - 1, MATE_SCORE + 1
        for move in moves:
            undo = board.make_move(move)
            score = -self._negamax(board, opponent(color), self.depth - 1, -beta, -alpha)
            board.unmake_move(undo)

            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

            if self.use_alpha_beta and best_score > alpha:
                alpha = best_score

        # Break ties randomly so the AI is not perfectly predictable.
        return self._rng.choice(best_moves)

    def _negamax(self, board, color, depth, alpha, beta):
        moves = generate_legal_moves(board, color)
        if not moves:
            # No legal move: checkmate (bad for side to move) or stalemate.
            if is_in_check(board, color):
                return -MATE_SCORE - depth
            return 0

        if depth <= 0:
            return evaluate(board, color, use_placement=self.use_placement)

        if self.order_moves:
            moves = self._ordered(board, moves)

        best = -MATE_SCORE - 1
        for move in moves:
            undo = board.make_move(move)
            score = -self._negamax(board, opponent(color), depth - 1, -beta, -alpha)
            board.unmake_move(undo)
            if score > best:
                best = score
            if self.use_alpha_beta:
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break  # Opponent already has a better option elsewhere.
        return best

    def _ordered(self, board, moves):
        """Search captures first; better ordering makes pruning far cheaper."""
        def score(move):
            if not move.is_capture:
                return 0
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_value = victim.value if victim else 0
            attacker_value = attacker.value if attacker else 0
            # Most-valuable-victim / least-valuable-attacker ordering.
            return 10 * victim_value - attacker_value

        return sorted(moves, key=score, reverse=True)
