// Thin wrapper around the ChessQuest REST API. Every call returns the full
// game-state object the rest of the UI renders from.

const API_BASE = "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body && body.detail) detail = body.detail;
    } catch (err) {
      /* response had no JSON body */
    }
    throw new Error(detail);
  }
  return response.json();
}

export const api = {
  createGame(mode, difficulty = null, humanColor = "white") {
    return request("/games", {
      method: "POST",
      body: JSON.stringify({ mode, difficulty, human_color: humanColor }),
    });
  },
  getGame(id) {
    return request(`/games/${id}`);
  },
  move(id, fromSquare, toSquare, promotion = null) {
    return request(`/games/${id}/moves`, {
      method: "POST",
      body: JSON.stringify({
        from_square: fromSquare,
        to_square: toSquare,
        promotion,
      }),
    });
  },
  aiMove(id) {
    return request(`/games/${id}/ai-move`, { method: "POST" });
  },
  undo(id) {
    return request(`/games/${id}/undo`, { method: "POST" });
  },
  restart(id) {
    return request(`/games/${id}/restart`, { method: "POST" });
  },
};
