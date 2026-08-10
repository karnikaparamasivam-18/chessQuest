"""In-memory store of active games.

Games live in a plain dictionary keyed by a generated id -- there is no
database, matching the V1 scope. Because move and AI endpoints run in a thread
pool, each game carries its own lock so concurrent requests for the same game
are serialised. A server restart clears all games, which is acceptable for
local single-session play.
"""

import threading
import uuid

from chess_engine.game import Game


class GameStore:
    """Thread-safe registry of in-progress games."""

    def __init__(self):
        self._games = {}
        self._locks = {}
        self._guard = threading.Lock()

    def create(self, mode="local", difficulty=None, human_color="white"):
        game = Game(
            game_mode=mode, ai_difficulty=difficulty, human_color=human_color
        )
        game_id = uuid.uuid4().hex
        with self._guard:
            self._games[game_id] = game
            self._locks[game_id] = threading.RLock()
        return game_id, game

    def get(self, game_id):
        with self._guard:
            return self._games.get(game_id)

    def lock_for(self, game_id):
        """Return the per-game lock (or None if the game is unknown)."""
        with self._guard:
            return self._locks.get(game_id)

    def remove(self, game_id):
        with self._guard:
            self._games.pop(game_id, None)
            self._locks.pop(game_id, None)

    def count(self):
        with self._guard:
            return len(self._games)


# A single process-wide store shared by all requests.
store = GameStore()
