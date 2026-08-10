"""Master: deeper Minimax with Alpha-Beta pruning and positional evaluation.

Searches deeper than Thinker, prunes branches that cannot change the result,
orders captures first to make that pruning effective, and judges positions with
piece-square tables on top of material.
"""

from .base import SearchingAI


class MasterAI(SearchingAI):
    difficulty = "master"
    depth = 3
    use_alpha_beta = True
    order_moves = True
    use_placement = True
