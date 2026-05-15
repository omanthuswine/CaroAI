"""
main.py – Điểm khởi động chính của chương trình Cờ Caro AI.

Chạy:  python main.py          (từ bất kỳ thư mục nào)
       → Mở giao diện đồ họa Pygame

Cài đặt dependency (nếu chưa có):
       pip install pygame
"""

import os
import sys

# ── Fix đường dẫn: cho phép chạy từ bất kỳ thư mục nào ───────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Tắt tiếng ồn ALSA khi chạy trên Linux/WSL không có thiết bị âm thanh.
# Chỉ set nếu chưa có biến môi trường âm thanh nào được đặt sẵn.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# KHÔNG set SDL_VIDEODRIVER – để SDL tự chọn driver phù hợp với hệ thống.


def _check_pygame():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("=" * 55)
        print("  ❌  Thiếu thư viện Pygame!")
        print("  Cài đặt bằng lệnh:  pip install pygame")
        print("=" * 55)
        sys.exit(1)


if __name__ == "__main__":
    _check_pygame()

    import pygame
    pygame.init()

    from source.ui import run_gui
    run_gui()
