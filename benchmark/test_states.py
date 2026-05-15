"""
benchmark/test_states.py – 6 trạng thái bàn cờ kiểm thử theo yêu cầu Level 3.

Mỗi trạng thái được định nghĩa bằng danh sách các nước đi đã đánh.
"""

from source.board import Board, PLAYER, AI


def _build_board(moves: list[tuple]) -> Board:
    """
    Xây dựng trạng thái bàn cờ từ danh sách (row, col, player).
    """
    board = Board()
    for r, c, player in moves:
        board.place(r, c, player)
    return board


# ── Trạng thái 1: Đầu ván (vài nước đầu) ─────────────────────────────────────
STATE_EARLY = _build_board([
    (4, 4, PLAYER),
    (4, 5, AI),
    (3, 4, PLAYER),
    (5, 4, AI),
])

# ── Trạng thái 2: Giữa ván ────────────────────────────────────────────────────
STATE_MID = _build_board([
    (4, 4, PLAYER),
    (4, 5, AI),
    (3, 4, PLAYER),
    (5, 4, AI),
    (3, 3, PLAYER),
    (6, 4, AI),
    (2, 4, PLAYER),
    (3, 5, AI),
    (5, 5, PLAYER),
    (4, 6, AI),
])

# ── Trạng thái 3: Máy sắp thắng ngay (3 quân liên tiếp, cần đánh ô thứ 4) ───
STATE_AI_WIN = _build_board([
    (4, 4, AI),
    (4, 5, AI),
    (4, 6, AI),
    (2, 2, PLAYER),
    (3, 3, PLAYER),
])

# ── Trạng thái 4: Người chơi sắp thắng, máy cần chặn ─────────────────────────
STATE_MUST_BLOCK = _build_board([
    (3, 2, AI),
    (3, 3, PLAYER),
    (3, 4, PLAYER),
    (3, 5, PLAYER),
    (5, 5, AI),
    (6, 5, AI),
])

# ── Trạng thái 5: Hai bên đều tấn công ───────────────────────────────────────
STATE_DUAL_ATTACK = _build_board([
    (4, 4, PLAYER),
    (4, 5, AI),
    (5, 4, PLAYER),
    (5, 5, AI),
    (6, 4, PLAYER),
    (6, 5, AI),
    (3, 3, PLAYER),
    (3, 6, AI),
])

# ── Trạng thái 6: Bàn cờ có nhiều nước đi hợp lệ (stress-test) ───────────────
STATE_OPEN = _build_board([
    (4, 4, PLAYER),
    (4, 5, AI),
    (5, 3, PLAYER),
    (3, 6, AI),
    (6, 2, PLAYER),
    (2, 7, AI),
])

ALL_STATES = [
    ("Đầu ván",                  STATE_EARLY),
    ("Giữa ván",                 STATE_MID),
    ("Máy sắp thắng",            STATE_AI_WIN),
    ("Người sắp thắng / chặn",   STATE_MUST_BLOCK),
    ("Hai bên tấn công",         STATE_DUAL_ATTACK),
    ("Nhiều nước đi (stress)",   STATE_OPEN),
]
