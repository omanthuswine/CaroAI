"""
game.py – Điều khiển luồng chơi console (Human vs AI).
"""

from source.board import Board, PLAYER, AI, EMPTY, BOARD_N
from source.ai    import get_ai_move


def _parse_move(raw: str, n: int):
    """
    Phân tích chuỗi nhập từ người dùng dạng 'row col' hoặc 'row,col'.
    Input từ người dùng: 1-based (1 đến n)
    Trả về (row, col) hoặc None nếu không hợp lệ. (0-based nội bộ)
    """
    try:
        parts = raw.replace(",", " ").split()
        r, c = int(parts[0]), int(parts[1])
        # Chuyển từ 1-based sang 0-based
        r -= 1
        c -= 1
        if 0 <= r < n and 0 <= c < n:
            return r, c
    except (ValueError, IndexError):
        pass
    return None


def run_game(
    board_size:    int  = BOARD_N,
    ai_depth:      int  = 3,
    use_alpha_beta: bool = True,
    player_first:  bool = True,
):
    """
    Vòng lặp chính của game console.

    Parameters
    ----------
    board_size     : kích thước bàn cờ (mặc định 9)
    ai_depth       : độ sâu tìm kiếm của AI
    use_alpha_beta : thuật toán AI sử dụng
    player_first   : True → người đi trước (X), False → máy đi trước
    """
    board   = Board(board_size)
    algo_name = "Alpha-Beta" if use_alpha_beta else "Minimax"

    print("\n" + "=" * 50)
    print(f"  🎮  CỜ CARO  –  Người (X) vs Máy (O)")
    print(f"  Bàn cờ: {board_size}×{board_size}  |  Thuật toán: {algo_name}  |  Độ sâu: {ai_depth}")
    print("=" * 50)
    print(f"  Nhập nước đi dạng:  hàng cột  (ví dụ: 4 5, từ 1 đến {board_size})")
    print("  Gõ 'q' để thoát.\n")

    current = PLAYER if player_first else AI
    board.display()

    while True:
        result = board.game_over()
        if result is not None:
            _print_result(result)
            break

        if current == PLAYER:
            # ── Lượt người chơi ──────────────────────────────────────────────
            while True:
                raw = input("  Nước của bạn (hàng cột): ").strip()
                if raw.lower() == "q":
                    print("  Đã thoát game.")
                    return
                move = _parse_move(raw, board.n)
                if move is None:
                    print(f"  ⚠️  Nhập sai. Ví dụ hợp lệ: 4 5  (1–{board.n})")
                    continue
                r, c = move
                if not board.is_empty(r, c):
                    print("  ⚠️  Ô đó đã có quân! Chọn ô khác.")
                    continue
                board.place(r, c, PLAYER)
                break

            board.display(highlight=(r, c))
            current = AI

        else:
            # ── Lượt máy ─────────────────────────────────────────────────────
            print("  Máy đang suy nghĩ...")
            move = get_ai_move(board, depth=ai_depth,
                               use_alpha_beta=use_alpha_beta, verbose=True)
            if move is None:
                print("  Máy không tìm được nước đi!")
                break
            r, c = move
            board.place(r, c, AI)
            print(f"  🤖  Máy đánh vào: ({r+1}, {c+1})\n")
            board.display(highlight=(r, c))
            current = PLAYER


def _print_result(result: int) -> None:
    print("=" * 50)
    if result == PLAYER:
        print("  🎉  CHÚC MỪNG! Bạn đã thắng!")
    elif result == AI:
        print("  🤖  Máy thắng! Chơi lại nào.")
    else:
        print("  🤝  Hòa! Ván đấu cân bằng.")
    print("=" * 50 + "\n")
