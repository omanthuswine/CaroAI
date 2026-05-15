"""
ai.py – Thuật toán AI cho cờ Caro.

Có hai thuật toán riêng biệt:
    1. minimax()      – Minimax thuần tuý (Level 1)
    2. alpha_beta()   – Minimax + Alpha-Beta pruning (Level 2)

Cả hai đều:
    - Dùng chung hàm evaluate() từ evaluate.py
    - Có giới hạn độ sâu (depth limit)
    - Đếm số trạng thái đã xét (node_count)
    - Đo thời gian chạy
    - Trả về SearchResult(best_move, best_score, node_count, elapsed_time)

Tối ưu hoá:
    - Sắp xếp nước đi (move ordering) để Alpha-Beta cắt nhánh hiệu quả hơn.
    - Early-exit khi tìm được nước thắng ngay (score >= SCORE_WIN).
    - Giới hạn branching factor (MAX_BRANCHING) để kiểm soát thời gian chạy.
"""

from __future__ import annotations
import math
import time
from typing import Optional

from source.board    import Board, AI, PLAYER
from source.evaluate import evaluate, SCORE_WIN

# ── Cài đặt ──────────────────────────────────────────────────────────────────
MAX_BRANCHING = 18   # số nước ứng viên tối đa mỗi lượt


# ─────────────────────────────────────────────────────────────────────────────
# Sắp xếp và lọc nước đi
# ─────────────────────────────────────────────────────────────────────────────

def _ordered_moves(board: Board, moves: list[tuple], player: int) -> list[tuple]:
    """
    Sắp xếp nước đi theo độ hứa hẹn để AI xét nước thắng/chặn trước.

    Minimax thuần vẫn cho cùng giá trị tối ưu ở cùng độ sâu; Alpha-Beta
    được lợi lớn vì các nhánh tốt được duyệt sớm hơn → cắt nhiều hơn.
    """
    opponent = -player
    mid      = board.n // 2

    def line_potential(r: int, c: int, owner: int) -> int:
        """Ước lượng tiềm năng của nước đi tại (r, c) cho `owner`."""
        axes = [((0, 1), (0, -1)), ((1, 0), (-1, 0)),
                ((1, 1), (-1, -1)), ((1, -1), (-1, 1))]
        best = 0
        for (dr1, dc1), (dr2, dc2) in axes:
            left  = board._count_dir(r, c, dr1, dc1, owner)
            right = board._count_dir(r, c, dr2, dc2, owner)
            count = 1 + left + right
            open_ends = 0
            end1 = (r + dr1 * (left + 1),  c + dc1 * (left + 1))
            end2 = (r + dr2 * (right + 1), c + dc2 * (right + 1))
            if board.is_empty(*end1):
                open_ends += 1
            if board.is_empty(*end2):
                open_ends += 1
            if count >= 4:
                best = max(best, SCORE_WIN)
            else:
                best = max(best, count * count * 100 + open_ends * 25)
        return best

    def move_priority(move: tuple) -> tuple:
        r, c = move

        board.place(r, c, player)
        wins_now       = (board.game_over() == player)
        own_potential  = line_potential(r, c, player)
        board.undo(r, c)

        board.place(r, c, opponent)
        blocks_win         = (board.game_over() == opponent)
        opponent_potential = line_potential(r, c, opponent)
        board.undo(r, c)

        tactical = 0
        if wins_now:
            tactical += 2 * SCORE_WIN
        if blocks_win:
            tactical += SCORE_WIN

        center_bonus = -(abs(r - mid) + abs(c - mid))
        return tactical + own_potential + opponent_potential // 2, center_bonus, -r, -c

    return sorted(moves, key=move_priority, reverse=True)


def _candidate_search_moves(board: Board, player: int) -> list[tuple]:
    """Lấy các nước ứng viên tốt nhất (tối đa MAX_BRANCHING) đã sắp xếp."""
    return _ordered_moves(board, board.candidate_moves(), player)[:MAX_BRANCHING]


def _winning_moves(board: Board, moves: list[tuple], player: int) -> list[tuple]:
    """Tìm các nước giúp `player` thắng ngay ở trạng thái hiện tại."""
    wins = []
    for r, c in moves:
        board.place(r, c, player)
        if board.game_over() == player:
            wins.append((r, c))
        board.undo(r, c)
    return wins


def _tactical_moves(board: Board, player: int) -> list[tuple]:
    """
    Ưu tiên tình huống bắt buộc: thắng ngay → chặn đối thủ thắng → thông thường.
    Giúp AI không bỏ lỡ nước thắng/chặn hiển nhiên.
    """
    moves = _candidate_search_moves(board, player)

    winning = _winning_moves(board, moves, player)
    if winning:
        return winning

    blocking = _winning_moves(board, moves, -player)
    if blocking:
        return blocking

    return moves


# ─────────────────────────────────────────────────────────────────────────────
# Lớp kết quả tìm kiếm
# ─────────────────────────────────────────────────────────────────────────────

class SearchResult:
    """Đóng gói kết quả sau mỗi lần gọi thuật toán."""

    def __init__(
        self,
        move:      Optional[tuple],
        score:     int,
        nodes:     int,
        elapsed:   float,
        depth:     int,
        algorithm: str,
    ):
        self.move      = move       # (row, col) tốt nhất
        self.score     = score      # điểm đánh giá
        self.nodes     = nodes      # số trạng thái đã xét
        self.elapsed   = elapsed    # thời gian (giây)
        self.depth     = depth      # độ sâu tìm kiếm
        self.algorithm = algorithm  # "minimax" | "alpha_beta"

    def __str__(self) -> str:
        return (
            f"[{self.algorithm.upper()}] "
            f"Nuoc di: {self.move}  |  "
            f"Diem: {self.score}  |  "
            f"Do sau: {self.depth}  |  "
            f"Trang thai xet: {self.nodes:,}  |  "
            f"Thoi gian: {self.elapsed:.4f}s"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 1.  MINIMAX (không cắt nhánh)
# ─────────────────────────────────────────────────────────────────────────────

def minimax(board: Board, depth: int, is_maximizing: bool) -> SearchResult:
    """
    Điểm vào công khai cho thuật toán Minimax.

    Parameters
    ----------
    board          : trạng thái hiện tại của bàn cờ
    depth          : độ sâu tìm kiếm tối đa
    is_maximizing  : True nếu đến lượt MAX (PLAYER), False nếu đến lượt MIN (AI)

    Returns
    -------
    SearchResult chứa nước đi tốt nhất và các thông số thống kê.
    """
    counter = [0]       # dùng list để truyền tham chiếu vào hàm đệ quy
    start   = time.perf_counter()

    best_score, best_move = _minimax_rec(board, depth, is_maximizing, counter)

    elapsed = time.perf_counter() - start
    return SearchResult(
        move      = best_move,
        score     = best_score,
        nodes     = counter[0],
        elapsed   = elapsed,
        depth     = depth,
        algorithm = "minimax",
    )


def _minimax_rec(
    board:        Board,
    depth:        int,
    is_maximizing: bool,
    counter:      list,
) -> tuple:
    """
    Hàm đệ quy nội bộ của Minimax.

    Trả về (score, move) tốt nhất tại trạng thái hiện tại.
    `move` chỉ có ý nghĩa ở lớp ngoài cùng (depth ban đầu).

    Tối ưu: early-exit khi tìm được nước thắng (score >= SCORE_WIN),
    tránh duyệt thêm các nhánh không cần thiết.
    """
    counter[0] += 1   # đếm một trạng thái

    # ── Điều kiện dừng ───────────────────────────────────────────────────────
    result = board.game_over()
    if result is not None:
        if result == PLAYER:
            return  SCORE_WIN, None
        elif result == AI:
            return -SCORE_WIN, None
        else:
            return 0, None          # hoà

    if depth == 0:
        return evaluate(board), None   # dùng hàm đánh giá heuristic

    # ── Sinh nước đi ứng viên ────────────────────────────────────────────────
    current_player = PLAYER if is_maximizing else AI
    moves = _tactical_moves(board, current_player)
    if not moves:
        return evaluate(board), None

    # ── MAX player (PLAYER / X) ───────────────────────────────────────────────
    if is_maximizing:
        best_score = -math.inf
        best_move  = moves[0]

        for r, c in moves:
            board.place(r, c, PLAYER)
            score, _ = _minimax_rec(board, depth - 1, False, counter)
            board.undo(r, c)

            if score > best_score:
                best_score = score
                best_move  = (r, c)

            # Early-exit: không thể làm tốt hơn thắng ngay
            if best_score >= SCORE_WIN:
                break

        return best_score, best_move

    # ── MIN player (AI / O) ───────────────────────────────────────────────────
    else:
        best_score = math.inf
        best_move  = moves[0]

        for r, c in moves:
            board.place(r, c, AI)
            score, _ = _minimax_rec(board, depth - 1, True, counter)
            board.undo(r, c)

            if score < best_score:
                best_score = score
                best_move  = (r, c)

            # Early-exit: không thể làm tệ hơn thua ngay
            if best_score <= -SCORE_WIN:
                break

        return best_score, best_move


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ALPHA-BETA PRUNING
# ─────────────────────────────────────────────────────────────────────────────

def alpha_beta(board: Board, depth: int, is_maximizing: bool) -> SearchResult:
    """
    Điểm vào công khai cho thuật toán Alpha-Beta pruning.

    Parameters và Returns giống minimax() để dễ so sánh.
    """
    counter = [0]
    start   = time.perf_counter()

    best_score, best_move = _alpha_beta_rec(
        board,
        depth,
        is_maximizing,
        -math.inf,   # alpha: tốt nhất MAX đã tìm được
         math.inf,   # beta : tốt nhất MIN đã tìm được
        counter,
    )

    elapsed = time.perf_counter() - start
    return SearchResult(
        move      = best_move,
        score     = best_score,
        nodes     = counter[0],
        elapsed   = elapsed,
        depth     = depth,
        algorithm = "alpha_beta",
    )


def _alpha_beta_rec(
    board:        Board,
    depth:        int,
    is_maximizing: bool,
    alpha:        float,
    beta:         float,
    counter:      list,
) -> tuple:
    """
    Hàm đệ quy nội bộ của Alpha-Beta.

    alpha : giá trị tốt nhất mà MAX đã đảm bảo được (trên đường đi tới đây)
    beta  : giá trị tốt nhất mà MIN đã đảm bảo được (trên đường đi tới đây)

    Điều kiện cắt nhánh:
        Nếu beta <= alpha → dừng (nhánh này sẽ không bao giờ được chọn)
    """
    counter[0] += 1

    # ── Điều kiện dừng ───────────────────────────────────────────────────────
    result = board.game_over()
    if result is not None:
        if result == PLAYER:
            return  SCORE_WIN, None
        elif result == AI:
            return -SCORE_WIN, None
        else:
            return 0, None

    if depth == 0:
        return evaluate(board), None

    current_player = PLAYER if is_maximizing else AI
    moves = _tactical_moves(board, current_player)
    if not moves:
        return evaluate(board), None

    # ── MAX player ────────────────────────────────────────────────────────────
    if is_maximizing:
        best_score = -math.inf
        best_move  = moves[0]

        for r, c in moves:
            board.place(r, c, PLAYER)
            score, _ = _alpha_beta_rec(board, depth - 1, False, alpha, beta, counter)
            board.undo(r, c)

            if score > best_score:
                best_score = score
                best_move  = (r, c)

            alpha = max(alpha, best_score)

            # ── Cắt nhánh Beta ─────────────────────────────────────────────
            if beta <= alpha:
                break   # MIN sẽ không bao giờ chọn nhánh này → cắt

        return best_score, best_move

    # ── MIN player ────────────────────────────────────────────────────────────
    else:
        best_score = math.inf
        best_move  = moves[0]

        for r, c in moves:
            board.place(r, c, AI)
            score, _ = _alpha_beta_rec(board, depth - 1, True, alpha, beta, counter)
            board.undo(r, c)

            if score < best_score:
                best_score = score
                best_move  = (r, c)

            beta = min(beta, best_score)

            # ── Cắt nhánh Alpha ────────────────────────────────────────────
            if beta <= alpha:
                break   # MAX sẽ không bao giờ chọn nhánh này → cắt

        return best_score, best_move


# ─────────────────────────────────────────────────────────────────────────────
# Hàm tiện ích: chạy AI và trả về (move, result)
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_move(
    board:          Board,
    depth:          int  = 3,
    use_alpha_beta: bool = True,
    verbose:        bool = True,
) -> tuple:
    """
    Giao diện đơn giản để lấy nước đi của AI.

    Returns
    -------
    (row, col) – nước đi tốt nhất của AI
    """
    algo   = alpha_beta if use_alpha_beta else minimax
    result = algo(board, depth, is_maximizing=False)   # AI là MIN player

    if verbose:
        print(f"\n  {result}")

    return result.move


def get_ai_result(
    board:          Board,
    depth:          int  = 3,
    use_alpha_beta: bool = True,
) -> "SearchResult":
    """
    Giống get_ai_move nhưng trả về SearchResult đầy đủ (dùng trong GUI).
    """
    algo = alpha_beta if use_alpha_beta else minimax
    return algo(board, depth, is_maximizing=False)
