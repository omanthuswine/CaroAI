"""
benchmark/runner.py – Chạy Minimax và Alpha-Beta trên các trạng thái kiểm thử
và in bảng kết quả theo yêu cầu Level 3.

Có hai chế độ sử dụng:
  1. Console:  run_benchmark()        → in bảng kết quả ra terminal
  2. GUI:      run_benchmark_data()   → trả về dữ liệu có cấu trúc cho BenchmarkScreen
"""

from source.ai             import minimax, alpha_beta
from benchmark.test_states import ALL_STATES

# ── Cài đặt benchmark ────────────────────────────────────────────────────────
DEPTHS = [1, 2, 3]   # thử nhiều độ sâu khác nhau


# =============================================================================
# Chế độ console
# =============================================================================

def run_benchmark() -> None:
    print("\n" + "=" * 80)
    print("  BENCHMARK: Minimax vs Alpha-Beta Pruning")
    print("=" * 80)

    for state_name, board in ALL_STATES:
        print(f"\n📋  Trạng thái: {state_name}")
        board.display()
        _benchmark_one_state(board, state_name)

    print("\n" + "=" * 80)
    print("  BENCHMARK HOÀN TẤT")
    print("=" * 80 + "\n")


def _benchmark_one_state(board, state_name: str) -> None:
    print(f"{'Thuật toán':<14} {'Độ sâu':>7} {'Nước đi':>10} "
          f"{'Điểm':>10} {'Trạng thái':>12} {'Thời gian(s)':>14}")
    print("-" * 72)

    for depth in DEPTHS:
        for algo_fn, algo_name in [(minimax, "Minimax"), (alpha_beta, "AlphaBeta")]:
            board_copy = board.copy()
            result = algo_fn(board_copy, depth, is_maximizing=False)
            print(
                f"  {algo_name:<12} {depth:>7}  "
                f"{str(result.move):>10}  "
                f"{result.score:>10,}  "
                f"{result.nodes:>12,}  "
                f"{result.elapsed:>13.4f}s"
            )

    print()
    # Dùng depth thứ hai (depth=2) để so sánh, hoặc depth cuối nếu chỉ có 1
    compare_depth = next((d for d in DEPTHS if d >= 2), DEPTHS[-1])
    _compare_moves(board, depth=compare_depth)


def _compare_moves(board, depth: int = 2) -> None:
    """So sánh nước đi và số trạng thái giữa hai thuật toán tại một độ sâu."""
    mm  = minimax   (board.copy(), depth, is_maximizing=False)
    ab  = alpha_beta(board.copy(), depth, is_maximizing=False)

    same_move = (mm.move == ab.move)
    reduction = (1 - ab.nodes / mm.nodes) * 100 if mm.nodes > 0 else 0.0

    print(f"  Độ sâu {depth}: Cùng nước đi? {'[Co]' if same_move else '[Khong]'}")
    print(f"  Alpha-Beta giảm {reduction:.1f}% trạng thái "
          f"({mm.nodes:,} -> {ab.nodes:,})")
    print(f"  Thời gian: Minimax {mm.elapsed:.4f}s  |  AlphaBeta {ab.elapsed:.4f}s")


# =============================================================================
# Chế độ GUI – trả về dữ liệu có cấu trúc
# =============================================================================

def run_benchmark_data(progress_cb=None) -> list:
    """
    Chạy benchmark và trả về dữ liệu có cấu trúc cho BenchmarkScreen.

    Parameters
    ----------
    progress_cb : callable(idx, name) | None
        Gọi mỗi khi bắt đầu chạy một trạng thái mới.
        idx  – chỉ số (0-based), name – tên trạng thái.

    Returns
    -------
    list[dict] – mỗi phần tử tương ứng một trạng thái kiểm thử:
        {
          "name": str,
          "depths": {
              depth: {
                  "minimax":    { move, score, nodes, elapsed },
                  "alpha_beta": { move, score, nodes, elapsed },
                  "same_move":  bool,
                  "reduction":  float   (% giảm số trạng thái)
              }
          }
        }
    """
    all_results = []

    for idx, (state_name, board) in enumerate(ALL_STATES):
        if progress_cb is not None:
            progress_cb(idx, state_name)

        state_result = {"name": state_name, "depths": {}}

        for depth in DEPTHS:
            depth_result = {}

            for algo_fn, algo_key in [(minimax, "minimax"), (alpha_beta, "alpha_beta")]:
                board_copy = board.copy()
                res = algo_fn(board_copy, depth, is_maximizing=False)
                depth_result[algo_key] = {
                    "move":    res.move,
                    "score":   res.score,
                    "nodes":   res.nodes,
                    "elapsed": res.elapsed,
                }

            # So sánh
            mm_d = depth_result["minimax"]
            ab_d = depth_result["alpha_beta"]
            reduction = (
                (1 - ab_d["nodes"] / mm_d["nodes"]) * 100
                if mm_d["nodes"] > 0 else 0.0
            )
            depth_result["same_move"] = (mm_d["move"] == ab_d["move"])
            depth_result["reduction"] = reduction

            state_result["depths"][depth] = depth_result

        all_results.append(state_result)

    return all_results


if __name__ == "__main__":
    run_benchmark()
