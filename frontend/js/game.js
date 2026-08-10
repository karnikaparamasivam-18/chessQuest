// ChessQuest frontend controller: screen flow, board rendering, input handling,
// move animation, computer turns, and audio cues. All game rules live on the
// server; this file only renders state and relays the player's intent.

import { api } from "./api.js";
import { sounds } from "./audio.js";
import { glyphFor } from "./pieces.js";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

const DIFFICULTY_LABELS = {
  beginner: "Beginner",
  thinker: "Thinker",
  master: "Master",
};

const ui = {
  gameId: null,
  state: null,
  mode: "local",
  difficulty: null,
  humanColor: "white",
  bottomColor: "white",
  chosenColor: "white", // selection on the difficulty screen (white/black/random)
  selected: null,
  legalTargets: new Map(), // square name -> move object
  busy: false,
};

// --------------------------------------------------------------- screens
function showScreen(id) {
  document.querySelectorAll(".screen").forEach((el) => {
    el.classList.toggle("active", el.id === id);
  });
}

function setEndOverlay(visible) {
  document.getElementById("overlay-end").classList.toggle("visible", visible);
}

// ------------------------------------------------------------ square helpers
function squareName(row, col) {
  return `${FILES[col]}${8 - row}`;
}

function squareElement(name) {
  return document.querySelector(`[data-square="${name}"]`);
}

// Board rows/cols in display order, honouring the side shown at the bottom.
function displayOrder() {
  const rows = [0, 1, 2, 3, 4, 5, 6, 7];
  const cols = [0, 1, 2, 3, 4, 5, 6, 7];
  if (ui.bottomColor === "black") {
    rows.reverse();
    cols.reverse();
  }
  return { rows, cols };
}

// ----------------------------------------------------------------- rendering
function buildBoard() {
  const board = document.getElementById("board");
  board.innerHTML = "";
  const { rows, cols } = displayOrder();

  rows.forEach((row, rowIndex) => {
    cols.forEach((col, colIndex) => {
      const name = squareName(row, col);
      const square = document.createElement("div");
      square.className = `square ${(row + col) % 2 === 0 ? "light" : "dark"}`;
      square.dataset.square = name;

      // Edge coordinates: ranks down the left edge, files along the bottom.
      if (colIndex === 0) square.dataset.rank = String(8 - row);
      if (rowIndex === rows.length - 1) square.dataset.file = FILES[col];

      square.addEventListener("click", () => onSquareClick(name));
      board.appendChild(square);
    });
  });
}

function renderPieces() {
  document.querySelectorAll(".square").forEach((square) => {
    const existing = square.querySelector(".piece");
    if (existing) existing.remove();
  });

  const grid = ui.state.board;
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const cell = grid[row][col];
      if (!cell) continue;
      const square = squareElement(squareName(row, col));
      const piece = document.createElement("div");
      piece.className = `piece ${cell.color}`;
      piece.textContent = glyphFor(cell.type);
      square.appendChild(piece);
    }
  }
}

function clearMarkers() {
  document.querySelectorAll(".square").forEach((square) => {
    square.classList.remove(
      "selected",
      "move-target",
      "capture-target",
      "last-move",
      "in-check"
    );
  });
}

function highlightLastMove() {
  const lm = ui.state.last_move;
  if (!lm) return;
  squareElement(lm.from)?.classList.add("last-move");
  squareElement(lm.to)?.classList.add("last-move");
}

function highlightCheck() {
  const st = ui.state;
  if (st.status !== "check" && st.status !== "checkmate") return;
  // The side to move is the one in check (or mated).
  const grid = st.board;
  for (let row = 0; row < 8; row += 1) {
    for (let col = 0; col < 8; col += 1) {
      const cell = grid[row][col];
      if (cell && cell.type === "king" && cell.color === st.turn) {
        squareElement(squareName(row, col))?.classList.add("in-check");
      }
    }
  }
}

function renderBoard() {
  renderPieces();
  clearMarkers();
  highlightLastMove();
  highlightCheck();
}

function animateLastMove() {
  const lm = ui.state.last_move;
  if (!lm) return;
  const toEl = squareElement(lm.to);
  const fromEl = squareElement(lm.from);
  const pieceEl = toEl?.querySelector(".piece");
  if (!toEl || !fromEl || !pieceEl) return;

  const fromRect = fromEl.getBoundingClientRect();
  const toRect = toEl.getBoundingClientRect();
  const dx = fromRect.left - toRect.left;
  const dy = fromRect.top - toRect.top;
  pieceEl.animate(
    [
      { transform: `translate(${dx}px, ${dy}px)` },
      { transform: "translate(0, 0)" },
    ],
    { duration: 220, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }
  );
}

// ------------------------------------------------------------------- panel
function renderPanel() {
  const st = ui.state;

  const turnLabel = document.getElementById("turn-label");
  const turnDot = document.getElementById("turn-dot");
  turnDot.className = `turn-dot ${st.turn}`;
  turnLabel.textContent = `${capitalize(st.turn)} to move`;

  const opponent = document.getElementById("opponent-info");
  if (st.game_mode === "computer") {
    opponent.textContent = `vs Computer — ${DIFFICULTY_LABELS[st.ai_difficulty]}`;
  } else {
    opponent.textContent = "Local two-player";
  }

  renderCaptured("captured-by-white", st.captured.black);
  renderCaptured("captured-by-black", st.captured.white);
  renderHistory(st.move_history);

  const undoBtn = document.getElementById("btn-undo");
  undoBtn.disabled = !st.can_undo || ui.busy;
  undoBtn.classList.toggle("hidden", st.game_mode !== "local");
}

function renderCaptured(elementId, pieceTypes) {
  const tray = document.getElementById(elementId);
  tray.innerHTML = "";
  pieceTypes.forEach((type) => {
    const span = document.createElement("span");
    span.className = "captured-piece";
    span.textContent = glyphFor(type);
    tray.appendChild(span);
  });
}

function renderHistory(history) {
  const list = document.getElementById("move-history");
  list.innerHTML = "";
  for (let i = 0; i < history.length; i += 2) {
    const item = document.createElement("li");
    const number = i / 2 + 1;
    const white = history[i] ? history[i].notation : "";
    const black = history[i + 1] ? history[i + 1].notation : "";
    item.innerHTML =
      `<span class="move-no">${number}.</span>` +
      `<span class="move-w">${white}</span>` +
      `<span class="move-b">${black}</span>`;
    list.appendChild(item);
  }
  list.parentElement.scrollTop = list.parentElement.scrollHeight;
}

// ----------------------------------------------------------------- input
function humanCanMove() {
  const st = ui.state;
  if (!st || st.is_over || ui.busy) return false;
  if (st.game_mode === "computer" && st.turn !== st.human_color) return false;
  return true;
}

function onSquareClick(name) {
  if (!humanCanMove()) return;

  // Clicking a legal target completes the move.
  if (ui.selected && ui.legalTargets.has(name)) {
    const move = ui.legalTargets.get(name);
    commitMove(move);
    return;
  }

  // Otherwise (re)select one of the side-to-move's own pieces.
  const piece = pieceAt(name);
  if (piece && piece.color === ui.state.turn) {
    selectSquare(name);
  } else {
    clearSelection();
  }
}

function pieceAt(name) {
  const col = FILES.indexOf(name[0]);
  const row = 8 - Number(name[1]);
  return ui.state.board[row][col];
}

function selectSquare(name) {
  clearSelection();
  ui.selected = name;
  ui.legalTargets = new Map();
  ui.state.legal_moves
    .filter((m) => m.from === name)
    .forEach((m) => ui.legalTargets.set(m.to, m));

  squareElement(name)?.classList.add("selected");
  ui.legalTargets.forEach((move, target) => {
    const cls = move.is_capture || move.is_en_passant ? "capture-target" : "move-target";
    squareElement(target)?.classList.add(cls);
  });
}

function clearSelection() {
  ui.selected = null;
  ui.legalTargets = new Map();
  document.querySelectorAll(".square").forEach((square) => {
    square.classList.remove("selected", "move-target", "capture-target");
  });
}

// ------------------------------------------------------------- move flow
async function commitMove(move) {
  clearSelection();
  ui.busy = true;
  try {
    const state = await api.move(ui.gameId, move.from, move.to, move.promotion);
    applyState(state, { animate: true });
    playMoveSounds(state);

    if (state.is_over) {
      finishGame(state);
    } else if (state.is_ai_turn) {
      await runAiTurn();
    }
  } catch (err) {
    showToast(err.message);
  } finally {
    ui.busy = false;
    renderPanel();
  }
}

async function runAiTurn() {
  showThinking(true);
  try {
    const state = await api.aiMove(ui.gameId);
    applyState(state, { animate: true });
    playMoveSounds(state);
    if (state.is_over) finishGame(state);
  } catch (err) {
    showToast(err.message);
  } finally {
    showThinking(false);
  }
}

function applyState(state, { animate = false } = {}) {
  ui.state = state;
  renderBoard();
  renderPanel();
  if (animate) animateLastMove();
}

function playMoveSounds(state) {
  if (state.status === "checkmate") {
    sounds.check();
    sounds.victory();
    return;
  }
  if (state.status === "check") {
    sounds.check();
    return;
  }
  const lm = state.last_move;
  if (lm && (lm.is_capture || lm.is_en_passant)) {
    sounds.capture();
  } else {
    sounds.move();
  }
}

// --------------------------------------------------------------- end game
function finishGame(state) {
  const title = document.getElementById("end-title");
  const detail = document.getElementById("end-detail");

  if (state.status === "checkmate") {
    title.textContent = "Checkmate!";
    detail.textContent = `${capitalize(state.winner)} wins the garden.`;
  } else if (state.status === "stalemate") {
    title.textContent = "Stalemate";
    detail.textContent = "A quiet draw settles over the garden.";
  } else if (state.status === "draw_fifty_move") {
    title.textContent = "Draw";
    detail.textContent = "Fifty moves without progress — it's a draw.";
  } else if (state.status === "draw_insufficient_material") {
    title.textContent = "Draw";
    detail.textContent = "Not enough pieces left to win — it's a draw.";
  } else {
    title.textContent = "Game Over";
    detail.textContent = "";
  }

  if (state.winner) launchPetals();
  setTimeout(() => setEndOverlay(true), 500);
}

// --------------------------------------------------------- thinking + toast
function showThinking(visible) {
  document.getElementById("thinking-indicator").classList.toggle("visible", visible);
}

let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 2600);
}

// ------------------------------------------------------------- game setup
async function startGame(mode, difficulty) {
  ui.mode = mode;
  ui.difficulty = difficulty;

  // Local games are always shown from White's side; against the computer the
  // player picks a side (Random resolves to White or Black here).
  let humanColor = "white";
  if (mode === "computer") {
    humanColor =
      ui.chosenColor === "random"
        ? Math.random() < 0.5
          ? "white"
          : "black"
        : ui.chosenColor;
  }
  ui.humanColor = humanColor;
  ui.bottomColor = humanColor;
  setEndOverlay(false);

  try {
    const state = await api.createGame(mode, difficulty, humanColor);
    ui.gameId = state.game_id;
    buildBoard();
    applyState(state);
    showScreen("screen-game");
    // If the human chose Black, the computer (White) opens the game.
    if (state.is_ai_turn) {
      ui.busy = true;
      await runAiTurn();
      ui.busy = false;
      renderPanel();
    }
  } catch (err) {
    showToast(err.message);
  }
}

async function newGame() {
  setEndOverlay(false);
  try {
    const state = await api.restart(ui.gameId);
    applyState(state);
  } catch (err) {
    showToast(err.message);
  }
}

async function undoMove() {
  if (!ui.state.can_undo) return;
  try {
    const state = await api.undo(ui.gameId);
    clearSelection();
    applyState(state);
  } catch (err) {
    showToast(err.message);
  }
}

// ------------------------------------------------------------- decoration
function launchPetals() {
  const layer = document.getElementById("petal-layer");
  for (let i = 0; i < 28; i += 1) {
    const petal = document.createElement("span");
    petal.className = "petal";
    petal.style.left = `${Math.random() * 100}%`;
    petal.style.animationDelay = `${Math.random() * 1.2}s`;
    petal.style.animationDuration = `${2.6 + Math.random() * 2}s`;
    layer.appendChild(petal);
    setTimeout(() => petal.remove(), 5200);
  }
}

function spawnFireflies() {
  const layer = document.getElementById("firefly-layer");
  if (!layer) return;
  for (let i = 0; i < 18; i += 1) {
    const fly = document.createElement("span");
    fly.className = "firefly";
    fly.style.left = `${Math.random() * 100}%`;
    fly.style.top = `${Math.random() * 100}%`;
    fly.style.animationDelay = `${Math.random() * 6}s`;
    fly.style.animationDuration = `${5 + Math.random() * 6}s`;
    layer.appendChild(fly);
  }
}

// ----------------------------------------------------------------- helpers
function capitalize(text) {
  return text ? text[0].toUpperCase() + text.slice(1) : text;
}

// --------------------------------------------------------------- wiring
function wireEvents() {
  document.getElementById("btn-play-friend").addEventListener("click", () => {
    sounds.click();
    startGame("local", null);
  });
  document.getElementById("btn-play-computer").addEventListener("click", () => {
    sounds.click();
    showScreen("screen-difficulty");
  });
  document.getElementById("btn-how").addEventListener("click", () => {
    document.getElementById("how-to-play").classList.toggle("open");
  });
  document.getElementById("btn-difficulty-back").addEventListener("click", () => {
    showScreen("screen-home");
  });
  document.querySelectorAll(".color-opt").forEach((opt) => {
    opt.addEventListener("click", () => {
      ui.chosenColor = opt.dataset.color;
      document
        .querySelectorAll(".color-opt")
        .forEach((o) => o.classList.toggle("selected", o === opt));
    });
  });
  document.querySelectorAll(".difficulty-card").forEach((card) => {
    card.addEventListener("click", () => {
      sounds.click();
      startGame("computer", card.dataset.difficulty);
    });
  });

  document.getElementById("btn-undo").addEventListener("click", undoMove);
  document.getElementById("btn-newgame").addEventListener("click", () => {
    sounds.click();
    newGame();
  });
  document.getElementById("btn-menu").addEventListener("click", () => {
    setEndOverlay(false);
    showScreen("screen-home");
  });
  document.getElementById("btn-sound").addEventListener("click", toggleSound);

  document.getElementById("btn-play-again").addEventListener("click", () => {
    sounds.click();
    newGame();
  });
  document.getElementById("btn-main-menu").addEventListener("click", () => {
    setEndOverlay(false);
    showScreen("screen-home");
  });
}

function toggleSound() {
  const nowMuted = !sounds.isMuted();
  sounds.setMuted(nowMuted);
  const btn = document.getElementById("btn-sound");
  btn.textContent = nowMuted ? "🔇" : "🔊";
  btn.setAttribute("aria-label", nowMuted ? "Unmute sounds" : "Mute sounds");
}

function init() {
  wireEvents();
  spawnFireflies();
  showScreen("screen-home");
}

document.addEventListener("DOMContentLoaded", init);
