"""
board.py – Biểu diễn trạng thái bàn cờ Caro.

Quy ước:
    0  = ô trống
    1  = X  (người chơi / maximizer)
   -1  = O  (máy     / minimizer)
Win condition: 4 quân liên tiếp (hàng ngang / dọc / chéo).
"""

from __future__ import annotations
from typing import Optional

# ── Hằng số ──────────────────────────────────────────────────────────────────
EMPTY   =  0
PLAYER  =  1   # X – người chơi (MAX)
AI      = -1   # O – máy       (MIN)
WIN_LEN =  4   # số quân liên tiếp để thắng
BOARD_N =  9   # kích thước bàn cờ (tối thiểu 9)

SYMBOL = {EMPTY: ".", PLAYER: "X", AI: "O"}


class Board:
    """
    Bàn cờ Caro N×N.

    Attributes
    ----------
    n : int                 kích thước bàn cờ
    grid : list[list[int]]  ma trận N×N (0 / 1 / -1)
    last_move : tuple|None  ô được đánh cuối cùng (row, col)
    last_player : int       người đánh nước cuối (1 hoặc -1)
    empty_cells : int       số ô trống còn lại
    """

    def __init__(self, n: int = BOARD_N):
        if n < BOARD_N:
            raise ValueError(f"Kích thước bàn cờ phải >= {BOARD_N}")
        self.n = n
        self.grid: list[list[int]] = [[EMPTY] * n for _ in range(n)]
        self.last_move: Optional[tuple] = None
        self.last_player: int = 0
        self.empty_cells: int = n * n
        self._history: list[tuple[Optional[tuple], int]] = []

    # ── Sao chép ─────────────────────────────────────────────────────────────
    def copy(self) -> "Board":
        b = Board(self.n)
        b.grid = [row[:] for row in self.grid]
        b.last_move   = self.last_move
        b.last_player = self.last_player
        b.empty_cells = self.empty_cells
        b._history = self._history[:]
        return b

    # ── Kiểm tra ô hợp lệ ────────────────────────────────────────────────────
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n

    def is_empty(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == EMPTY

    # ── Đánh quân ────────────────────────────────────────────────────────────
    def place(self, r: int, c: int, player: int) -> None:
        """Đặt quân player vào ô (r, c)."""
        assert player in (PLAYER, AI), "Người chơi phải là PLAYER hoặc AI"
        assert self.is_empty(r, c), f"Ô ({r},{c}) đã có quân!"
        self._history.append((self.last_move, self.last_player))
        self.grid[r][c] = player
        self.last_move   = (r, c)
        self.last_player = player
        self.empty_cells -= 1

    def undo(self, r: int, c: int) -> None:
        """Gỡ quân khỏi ô (r, c) – dùng trong Minimax."""
        assert self.in_bounds(r, c), f"Ô ({r},{c}) ngoài bàn cờ!"
        assert self.grid[r][c] != EMPTY, f"Ô ({r},{c}) đang trống!"
        self.grid[r][c] = EMPTY
        self.empty_cells += 1
        if self._history:
            self.last_move, self.last_player = self._history.pop()
        else:
            self.last_move = None
            self.last_player = 0

    # ── Đếm quân liên tiếp theo một hướng ───────────────────────────────────
    def _count_dir(self, r: int, c: int, dr: int, dc: int, player: int) -> int:
        count = 0
        nr, nc = r + dr, c + dc
        while self.in_bounds(nr, nc) and self.grid[nr][nc] == player:
            count += 1
            nr += dr
            nc += dc
        return count

    # ── Kiểm tra thắng tại ô (r, c) ─────────────────────────────────────────
    def is_winner(self, r: int, c: int, player: int) -> bool:
        """
        Trả về True nếu player có WIN_LEN quân liên tiếp đi qua ô (r,c).
        Kiểm tra 4 trục: ngang, dọc, chéo /, chéo \\
        """
        axes = [((0, 1),  (0, -1)),   # ngang
                ((1, 0),  (-1, 0)),   # dọc
                ((1, 1),  (-1, -1)),  # chéo \
                ((1, -1), (-1, 1))]   # chéo /

        for (dr1, dc1), (dr2, dc2) in axes:
            total = 1 \
                + self._count_dir(r, c, dr1, dc1, player) \
                + self._count_dir(r, c, dr2, dc2, player)
            if total >= WIN_LEN:
                return True
        return False

    # ── Trạng thái kết thúc ───────────────────────────────────────────────────
    def game_over(self) -> Optional[int]:
        """
        Trả về:
            1   nếu PLAYER thắng
           -1   nếu AI thắng
            0   nếu hoà (bàn cờ đầy)
            None nếu game chưa kết thúc
        """
        if self.last_move is None:
            return None
        r, c = self.last_move
        if self.is_winner(r, c, self.last_player):
            return self.last_player
        if self.empty_cells == 0:
            return 0   # hoà
        return None

    # ── Sinh nước đi ứng viên (candidate moves) ──────────────────────────────
    def candidate_moves(self, radius: int = 2) -> list[tuple]:
        """
        Trả về danh sách các ô trống nằm gần quân đã đánh (trong vòng `radius`).
        Giúp giảm không gian tìm kiếm đáng kể so với xét toàn bộ bàn cờ.

        Nếu bàn cờ trống hoàn toàn → trả về ô trung tâm.
        """
        if self.empty_cells == self.n * self.n:
            mid = self.n // 2
            return [(mid, mid)]

        candidates: set[tuple] = set()
        for r in range(self.n):
            for c in range(self.n):
                if self.grid[r][c] != EMPTY:
                    for dr in range(-radius, radius + 1):
                        for dc in range(-radius, radius + 1):
                            nr, nc = r + dr, c + dc
                            if self.is_empty(nr, nc):
                                candidates.add((nr, nc))
        mid = self.n // 2
        return sorted(candidates, key=lambda pos: (abs(pos[0] - mid) + abs(pos[1] - mid), pos[0], pos[1]))

    # ── Hiển thị bàn cờ ─────────────────────────────────────────────────────
    def display(self, highlight: Optional[tuple] = None) -> None:
        """In bàn cờ ra console. Nếu `highlight` không None thì đánh dấu ô đó."""
        row_width = len(str(self.n)) + 2
        col_header = f"{'':>{row_width}}" + "".join(f"{c:^3}" for c in range(1, self.n + 1))
        print(col_header)
        print(f"{'':>{row_width}}" + "---" * self.n)
        for r in range(self.n):
            row_str = f"{r+1:>{row_width-1}} "
            for c in range(self.n):
                sym = SYMBOL[self.grid[r][c]]
                if highlight and (r, c) == highlight:
                    sym = f"[{sym}]"
                else:
                    sym = f" {sym} "
                row_str += sym
            print(row_str)
        print()
