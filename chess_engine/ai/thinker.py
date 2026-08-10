"""Thinker: depth-limited Minimax without pruning.

Looks a couple of plies ahead, evaluating resulting positions on material, and
picks the line that comes out best. Enough to punish simple blunders.
"""

from .base import SearchingAI


class ThinkerAI(SearchingAI):
    difficulty = "thinker"
    depth = 2
    use_alpha_beta = False
    order_moves = False
    use_placement = False
