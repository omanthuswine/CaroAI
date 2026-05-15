"""
evaluate.py – Hàm đánh giá heuristic cho bàn cờ Caro.

Ý tưởng:
    Quét tất cả các cửa sổ (window) dài WIN_LEN theo 4 hướng.
    Mỗi cửa sổ chứa toàn X hoặc toàn O (+ ô trống) được gán điểm.
    Điểm dương → có lợi cho PLAYER (X / MAX).
    Điểm âm  → có lợi cho AI    (O / MIN).

Bảng điểm (có thể chỉnh tuỳ ý):
    4 quân liên tiếp   → ±1_000_000  (thắng)
    3 quân + 1 trống   → ±10_000
    2 quân + 2 trống   → ±100
    1 quân + 3 trống   → ±10
"""

from source.board import Board, PLAYER, AI, EMPTY, WIN_LEN

# ── Bảng điểm ────────────────────────────────────────────────────────────────
SCORE_WIN    = 1_000_000
SCORE_THREE  =    10_000
SCORE_TWO    =       100
SCORE_ONE    =        10

_PIECE_SCORES = {
    4: SCORE_WIN,
    3: SCORE_THREE,
    2: SCORE_TWO,
    1: SCORE_ONE,
}


def _window_score(window: list[int], player: int) -> int:
    """
    Tính điểm cho một cửa sổ (danh sách WIN_LEN ô).

    Trả về điểm dương nếu có lợi cho `player`, 0 nếu trung lập,
    hoặc số âm nếu cửa sổ bị chặn bởi đối thủ.
    """
    opponent = -player
    if opponent in window:
        return 0   # đối thủ đã có quân trong cửa sổ → bỏ qua

    count = window.count(player)
    return _PIECE_SCORES.get(count, 0)


def evaluate(board: Board) -> int:
    """
    Trả về điểm đánh giá của trạng thái `board` theo góc nhìn của PLAYER (MAX).

    Điểm > 0: PLAYER đang có lợi.
    Điểm < 0: AI đang có lợi.
    """
    n   = board.n
    grid = board.grid
    score = 0

    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # →, ↓, ↘, ↙

    for dr, dc in directions:
        for r in range(n):
            for c in range(n):
                # Lấy cửa sổ WIN_LEN ô bắt đầu từ (r, c)
                window: list[int] = []
                valid = True
                for k in range(WIN_LEN):
                    nr, nc = r + dr * k, c + dc * k
                    if not board.in_bounds(nr, nc):
                        valid = False
                        break
                    window.append(grid[nr][nc])

                if not valid:
                    continue

                score += _window_score(window, PLAYER)   # góc nhìn người chơi
                score -= _window_score(window, AI)       # góc nhìn máy (trừ)

    return score
