# Cờ Caro AI

Chương trình chơi cờ Caro giữa người chơi và máy tính cho bài thực hành Cơ sở Trí tuệ nhân tạo. Máy tính chọn nước đi bằng Minimax hoặc Alpha-Beta pruning với giới hạn độ sâu và hàm đánh giá heuristic.

README này chỉ hướng dẫn cài đặt, chạy chương trình và mô tả nhanh cấu trúc mã nguồn. Phần phân tích thuật toán, bảng kết quả thực nghiệm và nhận xét chi tiết được trình bày trong file báo cáo riêng.

## Yêu cầu môi trường

- Python 3.10 trở lên
- Pygame 2.0 trở lên

Cài thư viện:

```bash
python3 -m pip install -r requirements.txt
```

## Cách chạy chương trình

Chạy từ thư mục chứa file `main.py`:

```bash
python3 main.py
```

Chương trình mở giao diện đồ họa Pygame. Tại màn hình chính có thể chọn:

- Kích thước bàn cờ: `9x9`, `11x11`, `13x13`, `15x15`
- Độ sâu tìm kiếm của AI
- Thuật toán: `Minimax` hoặc `Alpha-Beta`
- Lượt đi trước: người chơi hoặc máy
- Chế độ chơi hoặc màn hình benchmark

Trong ván đấu:

- Người chơi dùng quân `X`
- Máy dùng quân `O`
- Bấm vào ô trống để đánh quân
- Sidebar hiển thị thuật toán, độ sâu, điểm đánh giá, số trạng thái đã xét và thời gian suy nghĩ của AI

## Luật chơi

- Bàn cờ có kích thước tối thiểu `9x9`
- Hai bên lần lượt đánh vào các ô trống
- Người thắng là người có 4 quân liên tiếp theo hàng ngang, hàng dọc hoặc đường chéo
- Không xét luật chặn hai đầu
- Nếu bàn cờ đầy và không có người thắng thì kết quả là hòa

## Chạy benchmark

Benchmark dùng các trạng thái kiểm thử trong `benchmark/test_states.py` để so sánh Minimax và Alpha-Beta trên cùng độ sâu và cùng hàm đánh giá.

Chạy trực tiếp:

```bash
python3 -m benchmark.runner
```

Kết quả benchmark gồm:

- Nước đi được chọn
- Giá trị đánh giá
- Độ sâu tìm kiếm
- Số trạng thái đã xét
- Thời gian chạy
- Tỷ lệ giảm số trạng thái của Alpha-Beta so với Minimax

## Chạy kiểm thử

```bash
python3 -m unittest discover -s tests -v
```

## Cấu trúc thư mục

```text
CaroAI_final/
├── main.py                  # Điểm khởi động giao diện Pygame
├── requirements.txt         # Thư viện cần cài đặt
├── README.md                # Hướng dẫn chạy chương trình
├── source/
│   ├── board.py             # Biểu diễn bàn cờ, luật đi, kiểm tra kết thúc
│   ├── evaluate.py          # Hàm đánh giá heuristic
│   ├── ai.py                # Minimax và Alpha-Beta pruning
│   ├── game.py              # Vòng lặp chơi console
│   └── ui.py                # Giao diện đồ họa Pygame
├── benchmark/
│   ├── test_states.py       # Các trạng thái kiểm thử
│   └── runner.py            # Chạy so sánh Minimax và Alpha-Beta
└── tests/
    └── test_caro_core.py    # Kiểm thử luật chơi và AI
```

## Các thành phần đáp ứng đề bài

- Biểu diễn trạng thái bàn cờ bằng ma trận hai chiều trong `source/board.py`
- Sinh nước đi hợp lệ và nước đi ứng viên gần các quân đã đánh
- Kiểm tra trạng thái kết thúc: thắng, thua, hòa hoặc chưa kết thúc
- Cài đặt Minimax có giới hạn độ sâu trong `source/ai.py`
- Cài đặt Alpha-Beta pruning dùng cùng hàm đánh giá với Minimax
- Hàm đánh giá trạng thái chưa kết thúc trong `source/evaluate.py`
- Ghi nhận nước đi, điểm đánh giá, số trạng thái đã xét và thời gian chạy
- Có benchmark để so sánh hai thuật toán trên nhiều trạng thái bàn cờ
