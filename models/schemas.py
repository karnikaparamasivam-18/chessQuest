"""Request bodies accepted by the API, validated by Pydantic."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

GameMode = Literal["local", "computer"]
Difficulty = Literal["beginner", "thinker", "master"]
Color = Literal["white", "black"]
PromotionPiece = Literal["queen", "rook", "bishop", "knight"]


class CreateGameRequest(BaseModel):
    """Options for starting a new game."""

    mode: GameMode = "local"
    difficulty: Optional[Difficulty] = None
    human_color: Color = "white"


class MoveRequest(BaseModel):
    """A move expressed as source/destination square names (e.g. "e2")."""

    from_square: str = Field(..., min_length=2, max_length=2)
    to_square: str = Field(..., min_length=2, max_length=2)
    promotion: Optional[PromotionPiece] = None
