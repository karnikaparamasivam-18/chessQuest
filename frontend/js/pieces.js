// Piece glyphs. The solid chess symbols are used for BOTH colours so the two
// sides share the same silhouette; colour comes entirely from CSS styling
// (ivory stone vs charcoal stone). This keeps White and Black visually equal
// and their traditional light/dark identity independent of the garden theme.

export const PIECE_GLYPHS = {
  king: "♚",
  queen: "♛",
  rook: "♜",
  bishop: "♝",
  knight: "♞",
  pawn: "♟",
};

export function glyphFor(pieceType) {
  return PIECE_GLYPHS[pieceType] || "";
}
