"""
ui.py – Giao diện Pygame cho Cờ Caro AI.

Gồm 3 màn hình:
    MenuScreen      – cài đặt và chọn chế độ chơi
    GameScreen      – màn hình chơi (Human vs AI) với sidebar thống kê AI
    BenchmarkScreen – chạy và hiển thị kết quả so sánh Minimax / Alpha-Beta
"""

from __future__ import annotations
import os
import sys
import threading
import pygame
import pygame.gfxdraw

from source.board import Board, PLAYER, AI, EMPTY, BOARD_N
from source.ai    import get_ai_result

# ─────────────────────────────────────────────────────────────────────────────
# Màu sắc
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK       = (13,  13,  22)
BG_CARD       = (22,  22,  34)
BG_BOARD      = (18,  18,  28)
GRID_COLOR    = (42,  42,  62)

ACCENT_ORANGE = (255, 138,  48)
ACCENT_GOLD   = (255, 198,  78)
ACCENT_GREEN  = ( 80, 200, 120)
ACCENT_RED    = (255,  80,  80)

X_COLOR       = (255,  95,  75)
O_COLOR       = ( 75, 175, 255)

TEXT_PRIMARY  = (238, 238, 248)
TEXT_MUTED    = (138, 138, 168)
TEXT_DIM      = ( 65,  65,  88)

BTN_NORMAL    = (32,  32,  52)
BTN_HOVER     = (48,  48,  72)
BTN_SELECTED  = (255, 138,  48)
BTN_SEL_FG    = (13,  13,  22)

WINDOW_W  = 960
WINDOW_H  = 720
SIDEBAR_W = 260
FPS       = 60

CELL_MAX = 58
PAD      = 44

# ─────────────────────────────────────────────────────────────────────────────
# Font
# ─────────────────────────────────────────────────────────────────────────────
pygame.init()


def _find_ttf(bold: bool = False) -> str | None:
    """Tìm font TTF hỗ trợ tiếng Việt có dấu, ưu tiên DejaVu / Noto / FreeSans."""

    # 1. Thử pygame.font.match_font để tìm font hệ thống theo tên
    viet_names = [
        "dejavusans",
        "notosans",
        "ubuntu",
        "freesans",
        "liberationsans",
        "arialunicode",
        "arial",
        "segoeui",
    ]
    for name in viet_names:
        try:
            path = pygame.font.match_font(name, bold=bold)
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass

    # 2. Fallback đường dẫn cứng
    win = os.environ.get("SystemRoot", os.environ.get("WINDIR", r"C:\Windows"))
    paths = [
        # Linux – DejaVu (hỗ trợ tiếng Việt tốt nhất)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        # Linux – FreeSans (hỗ trợ tiếng Việt)
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold
            else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Linux – Noto Sans
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        # Linux – Ubuntu
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf" if bold
            else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        # Linux – Liberation
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # Windows
        os.path.join(win, "Fonts", "segoeui.ttf"),
        os.path.join(win, "Fonts", "arial.ttf"),
        os.path.join(win, "Fonts", "calibri.ttf"),
        os.path.join(win, "Fonts", "tahoma.ttf"),
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def _make_font(size: int, bold: bool = False) -> pygame.font.Font:
    path = _find_ttf(bold)
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    return pygame.font.Font(None, size)


FONT_TITLE = _make_font(40, bold=True)
FONT_H2    = _make_font(20, bold=True)
FONT_BODY  = _make_font(17)
FONT_SM    = _make_font(14)
FONT_XS    = _make_font(12)


def _render(font: pygame.font.Font, text: str, color) -> pygame.Surface:
    try:
        surf = font.render(text, True, color)
        return surf
    except Exception:
        # Fallback: thay ký tự không in được bằng dấu ?
        safe = "".join(c if ord(c) < 0x10000 else "?" for c in text)
        try:
            return font.render(safe, True, color)
        except Exception:
            ascii_safe = text.encode("ascii", errors="replace").decode("ascii")
            return font.render(ascii_safe, True, color)


# ─────────────────────────────────────────────────────────────────────────────
# Tiện ích vẽ hình
# ─────────────────────────────────────────────────────────────────────────────
def fill_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def fill_rect_alpha(surface, color_rgb, alpha, rect, radius=10):
    tmp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(tmp, (*color_rgb, alpha), tmp.get_rect(), border_radius=radius)
    surface.blit(tmp, rect.topleft)


def glow_circle(surface, color, cx, cy, r, alpha=40):
    r = max(1, r)
    tmp = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    pygame.gfxdraw.filled_circle(tmp, r + 2, r + 2, r, (*color[:3], alpha))
    surface.blit(tmp, (cx - r - 2, cy - r - 2))


def draw_X(surface, cx, cy, r):
    glow_circle(surface, X_COLOR, cx, cy, max(1, r - 2) + 6, 30)
    d = max(3, int(r * 0.60))
    w = max(3, r // 4)
    pygame.draw.line(surface, X_COLOR, (cx-d, cy-d), (cx+d, cy+d), w+2)
    pygame.draw.line(surface, X_COLOR, (cx-d, cy+d), (cx+d, cy-d), w+2)
    pygame.draw.line(surface, (255, 200, 185), (cx-d+1, cy-d+1), (cx+d-1, cy+d-1), max(2, w-1))


def draw_O(surface, cx, cy, r):
    glow_circle(surface, O_COLOR, cx, cy, max(1, r - 2) + 6, 30)
    w = max(2, r // 4)
    pygame.draw.circle(surface, O_COLOR, (cx, cy), r, w+2)
    pygame.draw.circle(surface, (160, 215, 255), (cx, cy), r, max(1, w-1))
    if r >= 8:
        pygame.draw.circle(surface, (200, 235, 255), (cx - r//4, cy - r//4), max(1, r//6))


# ─────────────────────────────────────────────────────────────────────────────
# Nút bấm
# ─────────────────────────────────────────────────────────────────────────────
class Btn:
    def __init__(self, rect: pygame.Rect, label: str, value=None, selected=False):
        self.rect     = rect
        self.label    = label
        self.value    = value
        self.selected = selected
        self.hovered  = False

    def update(self, mp):
        self.hovered = self.rect.collidepoint(mp)

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))

    def draw(self, surf, font=None):
        if font is None:
            font = FONT_SM
        r = self.rect
        if self.selected:
            bg, fg, border = BTN_SELECTED, BTN_SEL_FG, BTN_SELECTED
        elif self.hovered:
            bg, fg, border = BTN_HOVER,    TEXT_PRIMARY, ACCENT_ORANGE
        else:
            bg, fg, border = BTN_NORMAL,   TEXT_MUTED,   GRID_COLOR
        pygame.draw.rect(surf, border, r, border_radius=8)
        pygame.draw.rect(surf, bg, r.inflate(-2, -2), border_radius=7)
        t = _render(font, self.label, fg)
        surf.blit(t, t.get_rect(center=r.center))


# ─────────────────────────────────────────────────────────────────────────────
# Màn hình Menu
# ─────────────────────────────────────────────────────────────────────────────
class MenuScreen:
    SIZES  = [9, 11, 13, 15]
    DEPTHS = [1, 2, 3, 4, 5]

    def __init__(self):
        self.board_size   = 9
        self.depth        = 3
        self.use_ab       = True
        self.player_first = True
        self._build()

    def _row_of_btns(self, labels_values, y, btn_w, btn_h=40, gap=12):
        n     = len(labels_values)
        total = n * btn_w + (n - 1) * gap
        x0    = (WINDOW_W - total) // 2
        return [
            Btn(pygame.Rect(x0 + i*(btn_w+gap), y, btn_w, btn_h), label, value=val)
            for i, (label, val) in enumerate(labels_values)
        ]

    def _build(self):
        GAP = 12
        H   = 40

        self.btn_size = self._row_of_btns(
            [(f"{s}x{s}", s) for s in self.SIZES],
            y=178, btn_w=108, btn_h=H, gap=GAP
        )
        for b in self.btn_size:
            b.selected = (b.value == self.board_size)

        self.btn_depth = self._row_of_btns(
            [(str(d), d) for d in self.DEPTHS],
            y=262, btn_w=80, btn_h=H, gap=GAP
        )
        for b in self.btn_depth:
            b.selected = (b.value == self.depth)

        self.btn_algo = self._row_of_btns(
            [("Alpha-Beta", True), ("Minimax", False)],
            y=346, btn_w=210, btn_h=H, gap=GAP
        )
        for b in self.btn_algo:
            b.selected = (b.value == self.use_ab)

        self.btn_first = self._row_of_btns(
            [("Bạn đi trước", True), ("Máy đi trước", False)],
            y=430, btn_w=210, btn_h=H, gap=GAP
        )
        for b in self.btn_first:
            b.selected = (b.value == self.player_first)

        cx = WINDOW_W // 2
        self.btn_start = Btn(pygame.Rect(cx - 140, 518, 280, 50), ">>  BẮT ĐẦU CHƠI")

        self.btn_benchmark = Btn(
            pygame.Rect(cx - 155, 580, 310, 40),
            "  BENCHMARK  (Minimax vs Alpha-Beta)"
        )

    def _set(self, group, val, attr):
        setattr(self, attr, val)
        for b in group:
            b.selected = (b.value == val)

    def handle_event(self, event) -> dict | None:
        """
        Trả về:
            dict   – config game khi nhấn Start
            "bm"   – khi nhấn Benchmark
            None   – bình thường
        """
        mp = pygame.mouse.get_pos()
        all_b = (self.btn_size + self.btn_depth + self.btn_algo
                 + self.btn_first + [self.btn_start, self.btn_benchmark])
        for b in all_b:
            b.update(mp)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for b in self.btn_size:
                if b.clicked(event): self._set(self.btn_size,  b.value, "board_size")
            for b in self.btn_depth:
                if b.clicked(event): self._set(self.btn_depth, b.value, "depth")
            for b in self.btn_algo:
                if b.clicked(event): self._set(self.btn_algo,  b.value, "use_ab")
            for b in self.btn_first:
                if b.clicked(event): self._set(self.btn_first, b.value, "player_first")
            if self.btn_start.clicked(event):
                return dict(board_size=self.board_size, depth=self.depth,
                            use_ab=self.use_ab, player_first=self.player_first)
            if self.btn_benchmark.clicked(event):
                return "bm"
        return None

    def draw(self, surf: pygame.Surface):
        surf.fill(BG_DARK)
        cx = WINDOW_W // 2

        t1 = _render(FONT_TITLE, "CỜ CARO AI", ACCENT_ORANGE)
        surf.blit(t1, t1.get_rect(centerx=cx, top=28))

        t2 = _render(FONT_SM, "Minimax  |  Cắt tỉa Alpha-Beta", TEXT_MUTED)
        surf.blit(t2, t2.get_rect(centerx=cx, top=78))

        pygame.draw.line(surf, GRID_COLOR, (cx-180, 104), (cx+180, 104), 1)

        for y, label in [
            (154, "KÍCH THƯỚC BÀN CỜ"),
            (238, "ĐỘ SÂU TÌM KIẾM (AI)"),
            (322, "THUẬT TOÁN"),
            (406, "LƯỢT ĐI ĐẦU TIÊN"),
        ]:
            lt = _render(FONT_SM, label, TEXT_MUTED)
            surf.blit(lt, lt.get_rect(centerx=cx, top=y))

        for b in self.btn_size + self.btn_depth + self.btn_algo + self.btn_first:
            b.draw(surf, FONT_SM)

        # Nút Start (cam nổi bật)
        bs = self.btn_start
        bs.update(pygame.mouse.get_pos())
        bg = ACCENT_GOLD if bs.hovered else ACCENT_ORANGE
        fill_rect(surf, bg, bs.rect, radius=10)
        pygame.draw.rect(surf, (255, 255, 255), bs.rect, border_radius=10, width=1)
        t = _render(FONT_H2, ">>  BẮT ĐẦU CHƠI", BTN_SEL_FG)
        surf.blit(t, t.get_rect(center=bs.rect.center))

        # Nút Benchmark (tối hơn, viền xanh)
        bb = self.btn_benchmark
        bb.update(pygame.mouse.get_pos())
        bm_bg     = BTN_HOVER if bb.hovered else BTN_NORMAL
        bm_border = ACCENT_GREEN
        fill_rect(surf, bm_bg, bb.rect, radius=8)
        pygame.draw.rect(surf, bm_border, bb.rect, border_radius=8, width=1)
        bt = _render(FONT_SM, "  BENCHMARK  (Minimax vs Alpha-Beta)", ACCENT_GREEN)
        surf.blit(bt, bt.get_rect(center=bb.rect.center))

        note = _render(FONT_XS, "X = Người  |  O = Máy  |  Thắng khi có 4 quân liên tiếp", TEXT_DIM)
        surf.blit(note, note.get_rect(centerx=cx, top=638))


# ─────────────────────────────────────────────────────────────────────────────
# Màn hình Game
# ─────────────────────────────────────────────────────────────────────────────
class GameScreen:
    def __init__(self, board_size, depth, use_ab, player_first):
        self.board_size   = board_size
        self.depth        = depth
        self.use_ab       = use_ab
        self.player_first = player_first
        self._last_ai_result = None   # SearchResult của nước AI cuối
        self._new_game()

    def _new_game(self):
        self.board     = Board(self.board_size)
        self.current   = PLAYER if self.player_first else AI
        self.result    = None
        self.last_move = None
        self.hover     = None
        self.history   = []
        self._thinking = False
        self._ai_result_pending = None   # SearchResult khi thread xong
        self._tick     = 0
        self._dots     = 0

        n   = self.board_size
        baw = WINDOW_W - SIDEBAR_W

        avail_w = baw - 2 * PAD
        avail_h = WINDOW_H - 2 * PAD
        cell    = min(CELL_MAX, avail_w // n, avail_h // n)
        cell    = max(cell, 20)
        self.cell = cell

        max_r        = (cell // 2) - 8
        self.stone_r = max(6, min(22, max_r))

        total_w = cell * n
        total_h = cell * n
        self.ox  = (baw    - total_w) // 2
        self.oy  = (WINDOW_H - total_h) // 2
        self.baw = baw

        if self.current == AI:
            self._ai_go()

    def _px(self, r: int, c: int) -> tuple[int, int]:
        return (self.ox + c * self.cell + self.cell // 2,
                self.oy + r * self.cell + self.cell // 2)

    def _cell_at(self, mx: int, my: int):
        rel_x = mx - self.ox
        rel_y = my - self.oy
        n     = self.board_size
        if rel_x < 0 or rel_x >= n * self.cell:
            return None
        if rel_y < 0 or rel_y >= n * self.cell:
            return None
        c = int(rel_x // self.cell)
        r = int(rel_y // self.cell)
        if 0 <= r < n and 0 <= c < n:
            return r, c
        return None

    def _ai_go(self):
        self._thinking = True
        self._ai_result_pending = None
        snap   = self.board.copy()
        depth  = self.depth
        use_ab = self.use_ab

        def think():
            res = get_ai_result(snap, depth=depth, use_alpha_beta=use_ab)
            self._ai_result_pending = res

        threading.Thread(target=think, daemon=True).start()

    def _place(self, r, c, player):
        self.board.place(r, c, player)
        self.last_move = (r, c)
        self.history.append((r, c, player))
        self.result = self.board.game_over()

    # ── Xử lý sự kiện ────────────────────────────────────────────────────────
    def handle_event(self, event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hover = self._cell_at(mx, my) if mx < self.baw else None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if mx >= self.baw:
                if self.btn_restart.collidepoint(event.pos):
                    self._new_game(); return None
                if self.btn_menu.collidepoint(event.pos):
                    return "menu"
                return None
            if self.result is None and self.current == PLAYER and not self._thinking:
                cell = self._cell_at(mx, my)
                if cell and self.board.is_empty(*cell):
                    self._place(*cell, PLAYER)
                    if self.result is None:
                        self.current = AI
                        self._ai_go()
        return None

    def update(self):
        self._tick += 1
        if self._tick % 18 == 0:
            self._dots = (self._dots + 1) % 4
        if self._thinking and self._ai_result_pending is not None:
            self._thinking = False
            res = self._ai_result_pending
            self._ai_result_pending = None
            self._last_ai_result = res      # lưu stats để hiển thị sidebar
            if res.move and self.result is None:
                self._place(*res.move, AI)
                if self.result is None:
                    self.current = PLAYER

    # ── Vẽ ───────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_DARK)
        self._draw_board(surf)
        self._draw_sidebar(surf)

    def _draw_board(self, surf):
        n    = self.board_size
        cell = self.cell

        pygame.draw.rect(surf, BG_BOARD, (0, 0, self.baw, WINDOW_H))

        x_left  = self.ox
        x_right = self.ox + n * cell
        y_top   = self.oy
        y_bot   = self.oy + n * cell

        for i in range(n + 1):
            x = self.ox + i * cell
            pygame.draw.line(surf, GRID_COLOR, (x, y_top), (x, y_bot), 1)
            y = self.oy + i * cell
            pygame.draw.line(surf, GRID_COLOR, (x_left, y), (x_right, y), 1)

        for c in range(n):
            px = self.ox + c * cell + cell // 2
            lbl = _render(FONT_XS, str(c + 1), TEXT_DIM)
            surf.blit(lbl, lbl.get_rect(centerx=px, bottom=y_top - 3))

        for r in range(n):
            py = self.oy + r * cell + cell // 2
            lbl = _render(FONT_XS, chr(ord('A') + r), TEXT_DIM)
            surf.blit(lbl, lbl.get_rect(right=x_left - 3, centery=py))

        if n >= 9:
            m = n // 2
            q = max(2, n // 4)
            for rr, cc in [(m, m)] + [(m+dr, m+dc) for dr in [-q, q] for dc in [-q, q]]:
                if 0 <= rr <= n and 0 <= cc <= n:
                    gx = self.ox + cc * cell
                    gy = self.oy + rr * cell
                    pygame.draw.circle(surf, GRID_COLOR, (gx, gy), 3)

        if (self.hover and self.result is None
                and self.current == PLAYER and not self._thinking):
            hr, hc = self.hover
            if self.board.is_empty(hr, hc):
                hpx, hpy = self._px(hr, hc)
                sr = self.stone_r
                d  = max(3, int(sr * 0.60))
                tmp = pygame.Surface((sr*4, sr*4), pygame.SRCALPHA)
                w   = max(2, sr//4)
                cx2, cy2 = sr*2, sr*2
                pygame.draw.line(tmp, (*X_COLOR, 60), (cx2-d, cy2-d), (cx2+d, cy2+d), w+1)
                pygame.draw.line(tmp, (*X_COLOR, 60), (cx2-d, cy2+d), (cx2+d, cy2-d), w+1)
                surf.blit(tmp, (hpx - sr*2, hpy - sr*2))

        for r in range(n):
            for c in range(n):
                v = self.board.grid[r][c]
                if v == EMPTY:
                    continue
                px, py = self._px(r, c)
                sr     = self.stone_r

                sq = pygame.Rect(self.ox + c*cell + 2,
                                 self.oy + r*cell + 2,
                                 cell - 3, cell - 3)
                if v == PLAYER:
                    fill_rect_alpha(surf, X_COLOR, 18, sq, radius=4)
                    draw_X(surf, px, py, sr)
                    if self.last_move == (r, c):
                        pygame.draw.rect(surf, (*X_COLOR, 200), sq,
                                         border_radius=4, width=2)
                else:
                    fill_rect_alpha(surf, O_COLOR, 18, sq, radius=4)
                    draw_O(surf, px, py, sr)
                    if self.last_move == (r, c):
                        pygame.draw.rect(surf, (*O_COLOR, 200), sq,
                                         border_radius=4, width=2)

        if self.result in (PLAYER, AI) and self.last_move:
            self._highlight_win(surf)

        if self.result is not None:
            self._draw_overlay(surf)

    def _highlight_win(self, surf):
        r0, c0  = self.last_move
        winner  = self.result
        axes    = [((0,1),(0,-1)), ((1,0),(-1,0)), ((1,1),(-1,-1)), ((1,-1),(-1,1))]
        cell    = self.cell

        for (dr1,dc1),(dr2,dc2) in axes:
            cells = [(r0, c0)]
            for dr, dc in [(dr1,dc1),(dr2,dc2)]:
                nr, nc = r0+dr, c0+dc
                while self.board.in_bounds(nr,nc) and self.board.grid[nr][nc]==winner:
                    cells.append((nr, nc)); nr+=dr; nc+=dc
            if len(cells) >= 4:
                col = X_COLOR if winner==PLAYER else O_COLOR
                for wr,wc in cells:
                    sq = pygame.Rect(self.ox + wc*cell + 2,
                                     self.oy + wr*cell + 2,
                                     cell - 3, cell - 3)
                    pygame.draw.rect(surf, col, sq, border_radius=4, width=3)
                break

    def _draw_overlay(self, surf):
        aw = self.baw
        ov = pygame.Surface((aw, WINDOW_H), pygame.SRCALPHA)
        ov.fill((10, 10, 18, 155))
        surf.blit(ov, (0, 0))

        bw, bh = 380, 148
        bx = (aw-bw)//2; by = (WINDOW_H-bh)//2
        fill_rect(surf, BG_CARD, pygame.Rect(bx, by, bw, bh), radius=14)
        pygame.draw.rect(surf, GRID_COLOR, (bx,by,bw,bh), border_radius=14, width=1)

        if self.result == PLAYER:
            l1, l2, col = "CHÚC MỪNG! BẠN ĐÃ THẮNG!", "Hãy chơi lại để thử thách thêm.", X_COLOR
        elif self.result == AI:
            l1, l2, col = "MÁY THẮNG!", "Chơi lại và cố gắng hơn nhé.", O_COLOR
        else:
            l1, l2, col = "HÒA!", "Ván đấu cân bằng xuất sắc.", ACCENT_GOLD

        t1 = _render(FONT_H2, l1, col)
        t2 = _render(FONT_SM, l2, TEXT_MUTED)
        t3 = _render(FONT_XS, "Nhấn 'Chơi lại' ở thanh bên phải ->", TEXT_DIM)
        surf.blit(t1, t1.get_rect(centerx=aw//2, top=by+26))
        surf.blit(t2, t2.get_rect(centerx=aw//2, top=by+68))
        surf.blit(t3, t3.get_rect(centerx=aw//2, top=by+108))

    def _draw_sidebar(self, surf):
        sx  = self.baw
        sw  = SIDEBAR_W
        pad = 18
        x   = sx + pad
        csx = sx + sw // 2

        fill_rect(surf, BG_CARD, pygame.Rect(sx, 0, sw, WINDOW_H), radius=0)
        pygame.draw.line(surf, GRID_COLOR, (sx, 0), (sx, WINDOW_H), 1)

        y = 22
        t = _render(FONT_H2, "CỜ CARO AI", ACCENT_ORANGE)
        surf.blit(t, t.get_rect(centerx=csx, top=y)); y += 28
        pygame.draw.line(surf, GRID_COLOR, (x, y), (sx+sw-pad, y), 1); y += 10

        algo = "Alpha-Beta" if self.use_ab else "Minimax"
        for lbl, val in [
            ("Thuật toán", algo),
            ("Độ sâu",     str(self.depth)),
            ("Bàn cờ",     f"{self.board_size}x{self.board_size}"),
            ("Số nước",    str(len(self.history))),
        ]:
            lt = _render(FONT_SM, lbl, TEXT_MUTED)
            vt = _render(FONT_SM, val, TEXT_PRIMARY)
            surf.blit(lt, (x, y))
            surf.blit(vt, vt.get_rect(right=sx+sw-pad, top=y))
            y += 20

        y += 4
        pygame.draw.line(surf, GRID_COLOR, (x, y), (sx+sw-pad, y), 1); y += 10

        dots = "." * self._dots
        if self.result is not None:
            if self.result == PLAYER:   st, sc = "Bạn thắng!", X_COLOR
            elif self.result == AI:     st, sc = "Máy thắng!", O_COLOR
            else:                       st, sc = "Hòa!", ACCENT_GOLD
        elif self._thinking:            st, sc = f"Máy đang nghĩ{dots}", O_COLOR
        elif self.current == PLAYER:    st, sc = "Lượt của bạn", X_COLOR
        else:                           st, sc = "Lượt của máy", O_COLOR

        bar = pygame.Rect(x, y, sw-2*pad, 34)
        fill_rect_alpha(surf, sc, 30, bar, radius=8)
        pygame.draw.rect(surf, sc, bar, border_radius=8, width=1)
        ts = _render(FONT_SM, st, sc)
        surf.blit(ts, ts.get_rect(center=bar.center))
        y += 44

        draw_X(surf, x+12, y+12, 10)
        surf.blit(_render(FONT_SM, " = Bạn  (X)", TEXT_MUTED), (x+26, y+5))
        draw_O(surf, x+12, y+30, 10)
        surf.blit(_render(FONT_SM, " = Máy  (O)", TEXT_MUTED), (x+26, y+23))
        y += 50

        pygame.draw.line(surf, GRID_COLOR, (x, y), (sx+sw-pad, y), 1); y += 8

        # ── AI stats (nước đi cuối) ───────────────────────────────────────────
        surf.blit(_render(FONT_SM, "THỐNG KÊ AI", TEXT_MUTED), (x, y)); y += 18
        if self._last_ai_result:
            r = self._last_ai_result
            move_str = f"({r.move[0]+1},{r.move[1]+1})" if r.move else "-"
            for lbl, val in [
                ("Nước đi",      move_str),
                ("Nodes duyệt",  f"{r.nodes:,}"),
                ("Thời gian",    f"{r.elapsed:.3f}s"),
                ("Điểm đánh giá",f"{r.score:,}"),
            ]:
                lt = _render(FONT_XS, lbl, TEXT_MUTED)
                vt = _render(FONT_XS, val, TEXT_PRIMARY)
                surf.blit(lt, (x, y))
                surf.blit(vt, vt.get_rect(right=sx+sw-pad, top=y))
                y += 15
        else:
            surf.blit(_render(FONT_XS, "(chưa có nước nào)", TEXT_DIM), (x, y))
            y += 15

        y += 4
        pygame.draw.line(surf, GRID_COLOR, (x, y), (sx+sw-pad, y), 1); y += 8

        # ── Lịch sử nước đi ──────────────────────────────────────────────────
        surf.blit(_render(FONT_SM, "LỊCH SỬ NƯỚC ĐI", TEXT_MUTED), (x, y)); y += 18
        max_rows = (WINDOW_H - 128 - y) // 17
        for i, (mr, mc, mp) in enumerate(reversed(self.history[-max_rows:])):
            num     = len(self.history) - i
            sym     = "X" if mp==PLAYER else "O"
            col     = X_COLOR if mp==PLAYER else O_COLOR
            row_lbl = chr(ord('A') + mr)
            txt     = f"  {num:2d}.  {sym}  {row_lbl}{mc+1}"
            c_use   = col if i==0 else TEXT_DIM
            surf.blit(_render(FONT_XS, txt, c_use), (x, y)); y += 17

        btn_y = WINDOW_H - 110
        self.btn_restart = pygame.Rect(x, btn_y,    sw-2*pad, 40)
        self.btn_menu    = pygame.Rect(x, btn_y+48, sw-2*pad, 40)
        mp2 = pygame.mouse.get_pos()
        self._side_btn(surf, self.btn_restart, "Chơi lại",   ACCENT_ORANGE, mp2)
        self._side_btn(surf, self.btn_menu,    "Menu chính", BTN_NORMAL,    mp2)

    def _side_btn(self, surf, rect, label, style, mp):
        hov = rect.collidepoint(mp)
        if style == ACCENT_ORANGE:
            bg, fg = (ACCENT_GOLD if hov else ACCENT_ORANGE), BTN_SEL_FG
        else:
            bg, fg = (BTN_HOVER if hov else BTN_NORMAL), TEXT_PRIMARY
        fill_rect(surf, bg, rect, radius=9)
        t = _render(FONT_BODY, label, fg)
        surf.blit(t, t.get_rect(center=rect.center))


# ─────────────────────────────────────────────────────────────────────────────
# Màn hình Benchmark
# ─────────────────────────────────────────────────────────────────────────────
class BenchmarkScreen:
    """
    Chạy Minimax và Alpha-Beta trên 6 trạng thái kiểm thử trong background thread.
    Hiển thị bảng kết quả có thể cuộn được.

    Layout:
        - Tiêu đề + thanh tiến trình (khi đang chạy)
        - Bảng kết quả cuộn được (sau khi xong)
        - Nút "Quay lai Menu" ở cuối
    """

    # ── Hằng số layout bảng ──────────────────────────────────────────────────
    COLS = [
        # (tên cột, độ rộng px, căn lề)
        ("Thuật toán",    98, "left"),
        ("Độ sâu",        46, "center"),
        ("Nước đi",       80, "center"),
        ("Điểm",          92, "right"),
        ("Nodes",        100, "right"),
        ("Thời gian",     82, "right"),
    ]
    TABLE_W   = sum(c[1] for c in COLS)
    TABLE_X0  = (WINDOW_W - TABLE_W) // 2

    ROW_H    = 20
    HEAD_H   = 24
    STATE_H  = 28
    COMP_H   = 18
    SEP_H    = 14
    DEPTHS   = [1, 2, 3]

    def __init__(self):
        self._done     = False
        self._results  = []
        self._scroll   = 0
        self._prog_idx  = 0
        self._prog_name = "Dang chuan bi..."
        self._total     = 6          # số trạng thái trong ALL_STATES
        self._content_surf: pygame.Surface | None = None
        self._content_h = 0
        self._tick      = 0

        bw = 200
        self.btn_back = pygame.Rect(WINDOW_W//2 - bw//2, WINDOW_H - 50, bw, 36)

        threading.Thread(target=self._run, daemon=True).start()

    # ── Chạy benchmark trong thread riêng ────────────────────────────────────
    def _run(self):
        from benchmark.runner import run_benchmark_data

        def on_progress(idx, name):
            self._prog_idx  = idx + 1
            self._prog_name = name

        self._results = run_benchmark_data(progress_cb=on_progress)
        self._prog_idx = self._total
        self._build_surface()
        self._done = True

    # ── Xây dựng Surface nội dung (pre-render để scroll nhanh) ───────────────
    def _build_surface(self):
        per_state_h = (self.STATE_H + self.HEAD_H
                       + len(self.DEPTHS) * 2 * self.ROW_H
                       + len(self.DEPTHS) * self.COMP_H
                       + self.SEP_H + 8)
        total_h = len(self._results) * per_state_h + 40

        surf = pygame.Surface((WINDOW_W, total_h))
        surf.fill(BG_DARK)

        x0 = self.TABLE_X0
        tw = self.TABLE_W
        y  = 16

        for state in self._results:
            # Tiêu đề trạng thái
            th = _render(FONT_H2, f"[{state['name']}]", ACCENT_GOLD)
            surf.blit(th, (x0, y))
            y += self.STATE_H

            # Header cột
            self._draw_row(surf, [c[0] for c in self.COLS], y,
                           TEXT_MUTED, FONT_XS, bold_first=False)
            y += self.HEAD_H - 2
            pygame.draw.line(surf, GRID_COLOR, (x0, y), (x0 + tw, y), 1)
            y += 2

            # Dữ liệu
            for depth in self.DEPTHS:
                dd = state["depths"].get(depth, {})

                for algo_key, algo_label, col in [
                    ("minimax",    "Minimax",   TEXT_PRIMARY),
                    ("alpha_beta", "AlphaBeta", ACCENT_ORANGE),
                ]:
                    d = dd.get(algo_key, {})
                    mv  = d.get("move", None)
                    mvs = f"({mv[0]+1},{mv[1]+1})" if mv else "-"
                    row = [
                        algo_label,
                        str(depth),
                        mvs,
                        f"{d.get('score', 0):,}",
                        f"{d.get('nodes', 0):,}",
                        f"{d.get('elapsed', 0):.4f}s",
                    ]
                    self._draw_row(surf, row, y, col, FONT_XS)
                    y += self.ROW_H

                # So sánh depth này
                same  = dd.get("same_move", True)
                red   = dd.get("reduction",  0.0)
                mm_n  = dd.get("minimax",    {}).get("nodes", 0)
                ab_n  = dd.get("alpha_beta", {}).get("nodes", 0)
                chk   = "[Có]" if same else "[Không]"
                ccol  = ACCENT_GREEN if same else ACCENT_RED
                comp  = (f"  Độ sâu {depth}: Cùng nước đi? {chk}  |  "
                         f"AlphaBeta giảm {red:.1f}%  "
                         f"({mm_n:,} -> {ab_n:,})")
                surf.blit(_render(FONT_XS, comp, ccol), (x0, y))
                y += self.COMP_H

            y += self.SEP_H - 4
            pygame.draw.line(surf, (38, 38, 58), (x0 - 10, y), (x0 + tw + 10, y), 1)
            y += 8

        self._content_surf = surf
        self._content_h    = total_h

    def _draw_row(self, surf, values, y, color, font, bold_first=True):
        x = self.TABLE_X0
        for i, ((_, w, align), val) in enumerate(zip(self.COLS, values)):
            use_col = ACCENT_ORANGE if (bold_first and i == 0 and val == "AlphaBeta") else color
            t = _render(font, val, use_col)
            r = pygame.Rect(x, y, w, self.ROW_H)
            if align == "right":
                surf.blit(t, t.get_rect(right=r.right - 3, centery=r.centery))
            elif align == "center":
                surf.blit(t, t.get_rect(center=r.center))
            else:
                surf.blit(t, t.get_rect(left=r.left + 3, centery=r.centery))
            x += w

    # ── Sự kiện ──────────────────────────────────────────────────────────────
    def handle_event(self, event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._scroll = max(0, self._scroll - 40)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._scroll += 40
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 40)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.collidepoint(event.pos):
                return "menu"
        return None

    def update(self):
        self._tick += 1
        if self._content_surf:
            view_h  = WINDOW_H - 88 - 56
            max_scr = max(0, self._content_h - view_h)
            self._scroll = min(self._scroll, max_scr)

    # ── Vẽ ───────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        surf.fill(BG_DARK)
        cx = WINDOW_W // 2

        # Tiêu đề
        t1 = _render(FONT_TITLE, "BENCHMARK", ACCENT_ORANGE)
        surf.blit(t1, t1.get_rect(centerx=cx, top=10))
        sub = _render(FONT_SM,
                      "Minimax vs Alpha-Beta  |  6 trạng thái  |  Độ sâu 1-3",
                      TEXT_MUTED)
        surf.blit(sub, sub.get_rect(centerx=cx, top=56))
        pygame.draw.line(surf, GRID_COLOR, (40, 80), (WINDOW_W - 40, 80), 1)

        VIEW_TOP = 86
        VIEW_BOT = WINDOW_H - 56
        VIEW_H   = VIEW_BOT - VIEW_TOP

        if not self._done:
            # Thanh tiến trình
            pct   = self._prog_idx / max(self._total, 1)
            bar_w = 420
            bar_x = cx - bar_w // 2
            bar_y = WINDOW_H // 2 - 22

            pygame.draw.rect(surf, BG_CARD, (bar_x, bar_y, bar_w, 18), border_radius=9)
            if pct > 0:
                pygame.draw.rect(surf, ACCENT_ORANGE,
                                 (bar_x, bar_y, int(bar_w * pct), 18),
                                 border_radius=9)
            pygame.draw.rect(surf, GRID_COLOR, (bar_x, bar_y, bar_w, 18),
                             border_radius=9, width=1)

            msg1 = _render(FONT_H2, "Đang chạy benchmark...", TEXT_PRIMARY)
            surf.blit(msg1, msg1.get_rect(centerx=cx, bottom=bar_y - 10))

            anim = "." * (1 + (self._tick // 20) % 3)
            msg2 = _render(FONT_SM,
                           f"Trạng thái {self._prog_idx}/{self._total}: "
                           f"{self._prog_name}{anim}",
                           TEXT_MUTED)
            surf.blit(msg2, msg2.get_rect(centerx=cx, top=bar_y + 26))

        else:
            # Vùng clip để cuộn
            clip_rect  = pygame.Rect(0, VIEW_TOP, WINDOW_W, VIEW_H)
            clip_surf  = surf.subsurface(clip_rect)
            if self._content_surf:
                clip_surf.blit(self._content_surf, (0, -self._scroll))

            # Scroll bar
            if self._content_h > VIEW_H:
                track_h  = VIEW_H
                thumb_h  = max(24, int(track_h * VIEW_H / self._content_h))
                progress = self._scroll / max(1, self._content_h - VIEW_H)
                thumb_y  = VIEW_TOP + int(progress * (track_h - thumb_h))
                pygame.draw.rect(surf, BG_CARD,
                                 (WINDOW_W - 7, VIEW_TOP, 5, track_h),
                                 border_radius=3)
                pygame.draw.rect(surf, GRID_COLOR,
                                 (WINDOW_W - 7, thumb_y, 5, thumb_h),
                                 border_radius=3)

            # Gợi ý cuộn
            hint = _render(FONT_XS, "Cuộn chuột hoặc phím UP/DOWN để xem thêm", TEXT_DIM)
            surf.blit(hint, hint.get_rect(centerx=cx, top=VIEW_BOT + 2))

        # Nút Quay lại
        mp  = pygame.mouse.get_pos()
        hov = self.btn_back.collidepoint(mp)
        fill_rect(surf, ACCENT_GOLD if hov else ACCENT_ORANGE, self.btn_back, radius=8)
        bt = _render(FONT_SM, "<  Quay lại Menu", BTN_SEL_FG)
        surf.blit(bt, bt.get_rect(center=self.btn_back.center))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def run_gui():
    pygame.display.set_caption("Co Caro AI")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock  = pygame.time.Clock()

    state = "menu"
    menu  = MenuScreen()
    game  = None
    bench = None

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if state == "menu":
                cfg = menu.handle_event(ev)
                if cfg == "bm":
                    bench = BenchmarkScreen()
                    state = "benchmark"
                elif isinstance(cfg, dict):
                    game  = GameScreen(**cfg)
                    state = "game"

            elif state == "game":
                r = game.handle_event(ev)
                if r == "menu":
                    menu = MenuScreen(); state = "menu"

            elif state == "benchmark":
                r = bench.handle_event(ev)
                if r == "menu":
                    menu = MenuScreen(); state = "menu"

        if state == "game" and game:
            game.update()
        if state == "benchmark" and bench:
            bench.update()

        if state == "menu":
            menu.draw(screen)
        elif state == "game" and game:
            game.draw(screen)
        elif state == "benchmark" and bench:
            bench.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)