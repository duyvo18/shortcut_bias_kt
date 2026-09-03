# Đặc tả triển khai — Thí điểm tín hiệu tắt trong truy vết tri thức

Tài liệu này dành cho người phụ trách mã nguồn, môi trường chạy và kiểm tra kỹ
thuật. Người chỉ cần biết mục tiêu, cách chạy và cách đọc kết quả có thể xem
[`README.md`](README.md). Đặc tả nghiên cứu gốc nằm trong [`PLAN.md`](PLAN.md).

## 1. Nguyên tắc kỹ thuật

Dự án được tổ chức theo một ranh giới rõ ràng:

- **pyKT** cung cấp bộ tiền xử lý, cách chia dữ liệu, lớp DKT/SAINT/AKT, vòng
  huấn luyện và cách lưu trạng thái mô hình.
- **Dự án này** cung cấp cấu hình YAML, chuẩn hóa bảng sự kiện, tính hồ sơ tín
  hiệu chỉ từ train, chọn mục tiêu, tạo các cặp dữ liệu đối chứng, thu dự đoán
  tại mục tiêu được bảo vệ và tính chênh lệch.

Không chép mã pyKT vào dự án. Phiên bản đang khóa là `pykt-toolkit==0.0.38`.

## 2. Cấu trúc mã nguồn

```text
src/shortcut_bias_pilot/
  __init__.py       Khai báo package và phiên bản
  cli.py            Các lệnh preprocess/smoke/screen
  config.py         Đọc và kiểm tra cấu hình YAML
  data.py           Đọc sequence pyKT thành bảng sự kiện chuẩn
  eligibility.py    Chọn mục tiêu và tính đặc trưng lịch sử
  env.py            Tải .env và cấu hình môi trường
  metrics.py        Tính chênh lệch cặp và khoảng bootstrap
  models.py         Tạo, huấn luyện và tải mô hình pyKT
  natural_metrics.py Chỉ số trên mục tiêu tự nhiên
  predictions.py    Dự đoán tại mục tiêu được bảo vệ
  probes.py         Tạo và kiểm tra cặp dữ liệu đối chứng
  profiles.py       Tính tỷ lệ nền item và hồ sơ nguồn
  pykt_adapter.py   Gọi bộ tiền xử lý và bộ chia dữ liệu pyKT
  workflow.py       Điều phối P0–P4
```

Các thư mục tài liệu:

```text
configs/             Cấu hình chạy thử và sàng lọc
case_cards/          Đặc tả IAP-01 và LGT-01
docs/                Quy tắc probe và ranh giới pyKT
outputs/             Kết quả sinh ra khi chạy, không phải mã nguồn
```

## 3. Môi trường và dependency

### 3.1. Cài đặt bằng uv

Không sửa tay danh sách phụ thuộc trong `pyproject.toml`. Khi cần thêm gói,
dùng:

```text
uv add <ten-goi>
```

Gói hiện tại:

- `pykt-toolkit==0.0.38`;
- `python-dotenv`;
- `pyyaml`;
- `pytest` trong nhóm phát triển.

Đồng bộ môi trường:

```text
uv sync
```

Python được khóa ở 3.11 qua `.python-version`. `uv.lock` ghi lại các phiên bản
được giải quyết, trong đó có các gói PyTorch/CUDA lớn.

### 3.2. GPU bắt buộc

Cấu hình yêu cầu `device: cuda`. `models.py` kiểm tra:

1. Torch có nhìn thấy CUDA;
2. mô hình pyKT được khởi tạo trên CUDA;
3. mô hình tải từ checkpoint vẫn nằm trên CUDA.

Nếu không đạt, chương trình dừng thay vì âm thầm chạy CPU.

Kiểm tra:

```text
uv run python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

### 3.3. Tải `.env`

`env.py` gọi `python-dotenv` khi package/CLI được nạp. Thứ tự tìm:

1. thư mục làm việc hiện tại;
2. các thư mục cha;
3. thư mục gốc của dự án.

Biến đã có trong shell không bị ghi đè. File mẫu:

```text
.env.sample
```

File làm việc thật là `.env`, không đưa vào Git.

## 4. Phân bổ CPU và GPU

### 4.1. Phần chạy GPU

Các phần phải chạy GPU:

- forward/backward của DKT, SAINT, AKT;
- huấn luyện;
- dự đoán tại mục tiêu;
- tải checkpoint vào mô hình để suy luận.

### 4.2. Phần chạy CPU

Các phần dùng CPU:

- đọc CSV;
- xử lý bảng bằng pandas;
- tiền xử lý và chia dữ liệu của pyKT;
- tính hồ sơ nguồn;
- tạo danh sách mục tiêu và cặp đối chứng;
- ghi CSV/JSON.

`cpu_threads` và `cpu_interop_threads` điều khiển các phép tính native của
Torch/NumPy/BLAS. Chúng không biến vòng lặp Python tuần tự của pyKT thành xử lý
song song.

Mặc định hiện tại:

```yaml
cpu_threads: 20
cpu_interop_threads: 2
device: cuda
```

Các biến `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` và
`NUMEXPR_NUM_THREADS` được đặt trước khi import pyKT ở các lệnh CLI.

### 4.3. Vì sao GPU có thể dùng thấp?

Bộ thu dự đoán hiện gọi forward từng mục tiêu. Mỗi lần gọi tạo một tensor nhỏ,
đợi GPU xử lý rồi chuyển một giá trị về CPU. Vì vậy CPU có thể bận ở vòng lặp
điều phối trong khi GPU chỉ hoạt động ngắn. Đây là giới hạn hiệu năng hiện tại,
không phải chủ trương chạy mô hình bằng CPU.

## 5. Hợp đồng cấu hình

### 5.1. Lớp cấu hình

`config.py` chuyển YAML thành ba nhóm:

- `DataConfig`: tên bộ dữ liệu, đường dẫn dữ liệu, metadata, độ dài chuỗi và số
  phần chia;
- `ThresholdConfig`: ngưỡng support, nhóm tỷ lệ nền, số mục tiêu và số lần
  bootstrap;
- `TrainConfig`: mô hình, hạt giống, phần dữ liệu, batch, epoch, learning rate,
  thiết bị và số luồng.

Giá trị trong YAML được ưu tiên hơn giá trị mặc định từ môi trường đối với số
luồng CPU.

### 5.2. Cấu hình chạy thử

`configs/smoke.yaml` dùng:

```yaml
models: [dkt, saint, akt]
seeds: [42]
fold: 0
epochs: 1
max_targets: 256
device: cuda
```

Mục tiêu là kiểm tra toàn bộ đường đi với chi phí giới hạn.

### 5.3. Cấu hình sàng lọc

`configs/screen.yaml` dùng:

```yaml
models: [dkt, saint, akt]
seeds: [42, 3407, 2024]
fold: 0
epochs: 200
max_targets: null
device: cuda
```

Đây là lần chạy dài; không tự động chạy khi cài đặt.

## 6. Luồng P0–P4

### P0 — Tiền xử lý

`pykt_adapter.py` gọi:

- `pykt.preprocess.nips_task34_preprocess.read_data_from_csv` cho Eedi;
- `pykt.preprocess.assist2009_preprocess.read_data_from_csv` cho ASSISTments;
- `split_datasets.main` để tạo chuỗi theo khái niệm;
- `split_datasets_que.main` để tạo chuỗi theo câu hỏi.

Riêng Eedi, adapter gọi trực tiếp hàm cấp thấp vì layout metadata nằm cạnh
`train_data/`, không nằm bên trong thư mục chứa file raw.

Kết quả được ghi dưới:

```text
outputs/pykt_data/<dataset>/
```

### P1 — Huấn luyện và dự đoán tự nhiên

`models.py` dùng:

- `pykt.datasets.init_dataset4train`;
- `pykt.models.init_model`;
- `pykt.models.train_model`.

Checkpoint được lưu dưới:

```text
outputs/checkpoints/<dataset>/<model>/seed_<seed>/fold_<fold>/qid_model.ckpt
```

`predictions.py` đọc phần lịch sử quan sát và câu hỏi/khái niệm của mục tiêu,
nhưng không truyền nhãn mục tiêu vào mô hình.

### P2 — Chọn mục tiêu và tính hồ sơ

`data.py` chuyển file sequence của pyKT thành bảng một dòng một sự kiện.
`eligibility.py` duyệt từng chuỗi theo thứ tự thời gian và giữ trạng thái tích
lũy:

- số tương tác cục bộ;
- tổng câu trả lời cục bộ;
- số tương tác ở khái niệm khác;
- tổng câu trả lời ở khái niệm khác;
- các câu trả lời cục bộ gần nhất.

Cách duyệt tích lũy này tránh tạo lại toàn bộ phần lịch sử cho từng mục tiêu.
Mỗi mục tiêu được giữ cùng `(sequence, position)`; phần lịch sử chỉ được tạo
khi cần dự đoán.

### P3 — Tạo cặp và tính chênh lệch

`probes.py` tạo `natural`, `plus`, `minus`. `predictions.py` gọi mô hình cho
mỗi biến thể. `metrics.py` ghép hai phía theo `base_target_id` và tính:

$$
\Delta_i = p_M(H_i^+) - p_M(H_i^-).
$$

Không tính AUC trên câu trả lời đã sửa.

### P4 — Manifest và review

`workflow.py` ghi:

- bảng mục tiêu;
- dự đoán tự nhiên và chỉ số AUC/BCE/Brier;
- dự đoán từng probe;
- summary của IAP-01/LGT-01;
- manifest nối các file với mô hình, seed và checkpoint.

Code không tự quyết định vượt G0–G4.

## 7. Các lớp mô hình pyKT

### DKT

Gọi mô hình bằng chuỗi khái niệm và câu trả lời quan sát. Dự đoán câu hỏi mục
tiêu được lấy từ vector xác suất của khái niệm mục tiêu ở trạng thái cuối.

### SAINT

Nhận chuỗi câu hỏi, khái niệm và câu trả lời lịch sử. Câu hỏi mục tiêu được
nối vào vị trí cuối; chỉ đọc xác suất ở vị trí đó.

### AKT

Nhận chuỗi khái niệm, câu trả lời và câu hỏi. Ở vị trí mục tiêu, câu trả lời
được dùng như giá trị truy vấn kỹ thuật theo cách pyKT 0.0.38 đang dùng trong
bộ đánh giá một bước; nhãn thật của mục tiêu vẫn không được đưa vào.

Thông số mô hình nằm trong `models.py` và được chọn từ `TrainConfig` cùng
`pykt_data_config.json`.

## 8. Cấu trúc artifact chi tiết

### Dữ liệu trung gian pyKT

| File | Nội dung |
| --- | --- |
| `data.txt` | Sáu dòng thông tin cho mỗi chuỗi người học. |
| `keyid2idx.json` | Ánh xạ mã gốc sang mã số dùng trong mô hình. |
| `pykt_data_config.json` | Số câu hỏi, số khái niệm, tên file, fold và độ dài chuỗi. |
| `train_valid*.csv` | Dữ liệu huấn luyện/kiểm định. |
| `test*.csv` | Dữ liệu test tự nhiên. |
| `*.pkl` | Bộ nhớ đệm do `KTDataset` tạo. |

### Bảng mục tiêu

Được ghi tại `outputs/targets/<dataset>/seed_<seed>.csv`, gồm định danh mục
tiêu, người học, câu hỏi, khái niệm, nhãn kiểm toán, vị trí, số tương tác cục bộ,
số tương tác xa, tỷ lệ trả lời và cờ đủ điều kiện.

### Dự đoán tự nhiên

Được ghi tại `outputs/predictions_natural/`. Mỗi dòng là một mục tiêu tự nhiên.
File JSON cùng tên có AUC, BCE/NLL và Brier.

### Dự đoán đối chứng

Được ghi tại `outputs/predictions_probe/`. Mỗi dòng là một mục tiêu và một biến
thể. Summary được ghi cạnh file chi tiết với hậu tố `_summary.csv`.

## 9. Kiểm tra kỹ thuật

### Kiểm tra cú pháp không cần dependency

```text
python3 -m compileall -q src
```

### Kiểm tra cấu hình trong môi trường uv

```text
uv run python -c "from shortcut_bias_pilot.config import PilotConfig; c=PilotConfig.from_yaml('configs/smoke.yaml'); c.validate(); print(c.train)"
```

### Kiểm tra GPU và package

```text
uv run python -c "import torch, pykt; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(pykt.__file__)"
```

### Smoke kỹ thuật nhẹ

Có thể kiểm tra load cấu hình và tạo cặp nhỏ bằng dữ liệu giả. Không dùng
`python3` hệ thống nếu cần import pandas/NumPy/Torch; dùng `uv run`.

### Chạy thực nghiệm

```text
uv run shortcut-pilot preprocess --config configs/smoke.yaml --dataset nips_task34
uv run shortcut-pilot smoke --config configs/smoke.yaml
uv run shortcut-pilot screen --config configs/screen.yaml
```

Ba lệnh cuối là workload thật. Đội triển khai cần tự quyết định khi chạy.

## 10. Giới hạn kỹ thuật cần biết

- pyKT 0.0.38 khá cũ và dùng các vòng lặp Python tuần tự trong tiền xử lý;
- DataLoader chuẩn của pyKT 0.0.38 trực tiếp tạo tensor CUDA, nên không tùy tiện
  tăng số worker tiến trình;
- bộ thu dự đoán hiện chưa gom nhiều mục tiêu thành một batch lớn;
- sự kiện nhiều khái niệm hiện dùng khái niệm đầu tiên sau bước mở rộng của pyKT;
- số liệu chỉ dùng tín hiệu nguồn và quyết định G1–G4 chưa tự động hóa hoàn toàn;
- chưa có cấu hình đối chứng chéo `assist2009` hoàn chỉnh;
- chưa có kiểm soát bán tổng hợp P5.

## 11. Quy tắc thay đổi mã

- Không sửa `pyproject.toml` bằng tay để thêm gói; dùng `uv add`.
- Không đưa dữ liệu thô hoặc artifact lớn vào thư mục tài liệu.
- Không đổi `test_natural` khi tạo phép kiểm tra.
- Không truyền nhãn mục tiêu vào input.
- Không dùng AUC trên prefix đã sửa.
- Khi đổi threshold hoặc cách tạo probe, phải cập nhật YAML, case card và ghi rõ
  ảnh hưởng trong báo cáo.
- Khi đổi cách đọc output pyKT, cần kiểm lại mapping target và vị trí dự đoán.
