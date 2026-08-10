"""Computer opponents at three strengths: Beginner, Thinker, and Master."""

from .base import ChessAI
from .beginner import BeginnerAI
from .master import MasterAI
from .thinker import ThinkerAI

# Difficulty identifiers exchanged with the API / frontend.
BEGINNER = "beginner"
THINKER = "thinker"
MASTER = "master"

_AI_BY_DIFFICULTY = {
    BEGINNER: BeginnerAI,
    THINKER: ThinkerAI,
    MASTER: MasterAI,
}


def create_ai(difficulty, seed=None):
    """Build an AI opponent for the given difficulty identifier."""
    try:
        ai_class = _AI_BY_DIFFICULTY[difficulty]
    except KeyError:
        raise ValueError(f"Unknown AI difficulty: {difficulty!r}")
    return ai_class(seed=seed)


__all__ = [
    "ChessAI",
    "BeginnerAI",
    "ThinkerAI",
    "MasterAI",
    "create_ai",
    "BEGINNER",
    "THINKER",
    "MASTER",
]
