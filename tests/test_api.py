"""End-to-end API tests driven through FastAPI's TestClient."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _create(client, **body):
    response = client.post("/api/games", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_local_game_returns_starting_position(client):
    state = _create(client, mode="local")
    assert state["turn"] == "white"
    assert state["status"] == "ongoing"
    assert len(state["legal_moves"]) == 20
    assert state["board"][0][0] == {"type": "rook", "color": "black"}
    assert state["board"][7][4] == {"type": "king", "color": "white"}


def test_submit_legal_move_updates_board(client):
    state = _create(client, mode="local")
    gid = state["game_id"]
    response = client.post(
        f"/api/games/{gid}/moves",
        json={"from_square": "e2", "to_square": "e4"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["turn"] == "black"
    assert updated["board"][4][4] == {"type": "pawn", "color": "white"}
    assert updated["board"][6][4] is None
    assert updated["move_history"][-1]["notation"] == "e2-e4"


def test_illegal_move_is_rejected(client):
    state = _create(client, mode="local")
    gid = state["game_id"]
    response = client.post(
        f"/api/games/{gid}/moves",
        json={"from_square": "e2", "to_square": "e5"},  # pawn can't jump 3
    )
    assert response.status_code == 400


def test_undo_in_local_game(client):
    state = _create(client, mode="local")
    gid = state["game_id"]
    client.post(f"/api/games/{gid}/moves", json={"from_square": "e2", "to_square": "e4"})
    response = client.post(f"/api/games/{gid}/undo")
    assert response.status_code == 200
    assert response.json()["turn"] == "white"
    assert len(response.json()["move_history"]) == 0


def test_computer_game_requires_difficulty(client):
    response = client.post("/api/games", json={"mode": "computer"})
    assert response.status_code == 400


def test_computer_ai_move_flow(client):
    state = _create(client, mode="computer", difficulty="beginner", human_color="white")
    gid = state["game_id"]
    # Human (white) moves first.
    client.post(f"/api/games/{gid}/moves", json={"from_square": "e2", "to_square": "e4"})
    # Now it is the AI's (black) turn.
    response = client.post(f"/api/games/{gid}/ai-move")
    assert response.status_code == 200
    after = response.json()
    assert after["turn"] == "white"  # AI replied, back to human
    assert len(after["move_history"]) == 2


def test_undo_blocked_in_computer_game(client):
    state = _create(client, mode="computer", difficulty="beginner")
    gid = state["game_id"]
    client.post(f"/api/games/{gid}/moves", json={"from_square": "e2", "to_square": "e4"})
    response = client.post(f"/api/games/{gid}/undo")
    assert response.status_code == 400


def test_ai_move_rejected_on_humans_turn(client):
    state = _create(client, mode="computer", difficulty="beginner")
    gid = state["game_id"]
    # It is the human's turn at the start; AI move should be refused.
    response = client.post(f"/api/games/{gid}/ai-move")
    assert response.status_code == 400


def test_restart_clears_history(client):
    state = _create(client, mode="local")
    gid = state["game_id"]
    client.post(f"/api/games/{gid}/moves", json={"from_square": "d2", "to_square": "d4"})
    response = client.post(f"/api/games/{gid}/restart")
    assert response.status_code == 200
    assert len(response.json()["move_history"]) == 0
    assert response.json()["turn"] == "white"


def test_unknown_game_returns_404(client):
    response = client.get("/api/games/does-not-exist")
    assert response.status_code == 404
