# Tóm tắt điều hành — Thí điểm kiểm tra tín hiệu tắt trong KT

## Mục đích

Đây là thí điểm của Chuyên đề 1 (CĐ1), được xây dựng theo
[`PLAN.md`](PLAN.md) và định hướng trong [`research_direction.pdf`](research_direction.pdf).

Mục tiêu là xem các mô hình **truy vết tri thức** có nhạy cảm quá mức với các
quy luật thống kê dễ khai thác hay không, trong khi bằng chứng trực tiếp về
khái niệm cần dự đoán được kiểm soát.

Thí điểm kiểm tra hai tín hiệu:

1. **Tỷ lệ đúng nền của câu hỏi:** câu hỏi thường được người học trả lời đúng
   hay sai trong tập huấn luyện.
2. **Xu hướng trả lời chung của người học:** người học thường trả lời đúng hay
   sai ở các khái niệm khác, ngoài khái niệm đang cần dự đoán.

> Kết quả chỉ nói về mức độ nhạy cảm của mô hình trong phép kiểm tra đã thiết kế. Một chênh lệch lớn không tự động có nghĩa là dữ liệu hoặc mô hình “bị thiên lệch tín hiệu tắt”. Độ khó câu hỏi và năng lực chung vẫn có thể là thông tin hợp lệ.

## Ai cần đọc tài liệu nào?

| Nhu cầu | Tài liệu |
| --- | --- |
| Muốn biết thí nghiệm làm gì và đọc kết quả ra sao | Tài liệu này |
| Muốn biết từng trường hợp kiểm tra được tạo như thế nào | [`case_cards/IAP-01.md`](case_cards/IAP-01.md), [`case_cards/LGT-01.md`](case_cards/LGT-01.md) |
| Muốn biết quy tắc bất biến của cặp kiểm tra | [`docs/probe_protocol.md`](docs/probe_protocol.md) |
| Muốn biết chi tiết cài đặt và cấu trúc mã | [`IMPLEMENTATION.md`](IMPLEMENTATION.md) |
| Muốn xem toàn bộ kế hoạch nghiên cứu | [`PLAN.md`](PLAN.md) |

## Phạm vi lần chạy đầu

- Bộ dữ liệu chính: `nips_task34` — Eedi/NeurIPS 2020.
- Mô hình: DKT, SAINT và AKT.
- Chạy thử: một phần chia dữ liệu, một hạt giống, một vòng huấn luyện, tối đa
  256 mục tiêu.
- Sàng lọc: một phần chia dữ liệu, ba hạt giống, thời gian huấn luyện dài hơn.
- `assist2009`: đối chứng chéo, chưa có cấu hình chính thức trong repository.

## Cần chuẩn bị một lần

Từ thư mục gốc của dự án:

```text
uv sync
cp .env.sample .env
```

Kiểm tra GPU:

```text
uv run python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"
```

Nếu lệnh trên không in ra tên GPU, chưa nên chạy thực nghiệm.

Trong các tệp cấu hình, thiết bị chạy mô hình được đặt là `device: cuda`.

## Cách chạy

### 1. Chuẩn bị dữ liệu

```text
uv run shortcut-pilot preprocess \
  --config configs/smoke.yaml \
  --dataset nips_task34
```

Bước này chỉ chuẩn bị dữ liệu cho pyKT và tạo các file trung gian. Chưa huấn
luyện mô hình, chưa tạo phép kiểm tra tín hiệu tắt.

### 2. Chạy thử toàn bộ quy trình

```text
uv run shortcut-pilot smoke --config configs/smoke.yaml
```

Lệnh này sẽ:

1. chuẩn bị dữ liệu;
2. huấn luyện DKT, SAINT và AKT;
3. lưu trạng thái mô hình;
4. tính hồ sơ tỷ lệ đúng nền từ tập huấn luyện;
5. chọn các mục tiêu đủ điều kiện;
6. tạo dự đoán tự nhiên;
7. tạo hai nhóm phép kiểm tra IAP-01 và LGT-01;
8. tính dự đoán cho hai phía `plus` và `minus`;
9. ghi chênh lệch và bảng tổng hợp.

Đây là lần chạy thật nhưng được giới hạn để kiểm tra pipeline. Không cần chạy
lại bước này nếu chỉ muốn đọc các file kết quả đã có.

### 3. Chạy sàng lọc chính

Chỉ chạy sau khi nhóm đã xem kết quả chạy thử:

```text
uv run shortcut-pilot screen --config configs/screen.yaml
```

Lệnh này chạy ba hạt giống và ngân sách huấn luyện dài hơn. Đây là phần chạy
chính theo `PLAN.md`; người dùng tự quyết định thời điểm chạy.

## Kết quả nằm ở đâu?

Các thư mục quan trọng:

```text
outputs/
  checkpoints/                 Trạng thái mô hình
  targets/                     Danh sách mục tiêu và điều kiện đủ
  predictions_natural/         Dự đoán trên dữ liệu tự nhiên
  predictions_probe/           Dự đoán của các phép kiểm tra đối chứng
  pykt_data/                   Dữ liệu trung gian do pyKT tạo
  smoke_manifest.json          Bảng theo dõi lần chạy thử
  screen_manifest.json         Bảng theo dõi lần sàng lọc
```

### Thứ tự nên xem

1. `outputs/<giai_doan>_manifest.json` để biết lần chạy đã tạo những gì.
2. `outputs/predictions_natural/.../*_metrics.json` để kiểm tra mô hình chạy
   bình thường.
3. `outputs/targets/...csv` để kiểm tra số mục tiêu và điều kiện đủ.
4. `outputs/predictions_probe/.../IAP-01_summary.csv` để xem trường hợp tỷ lệ
   nền của câu hỏi.
5. `outputs/predictions_probe/.../LGT-01_summary.csv` để xem trường hợp xu
   hướng trả lời chung.
6. Các file `IAP-01.csv` và `LGT-01.csv` chi tiết để xem từng mục tiêu bất
   thường.

## Các số liệu có ý nghĩa gì?

### Chỉ số trên dữ liệu tự nhiên

File `_metrics.json` có thể chứa:

- **AUC:** khả năng xếp đúng mục tiêu trả lời đúng cao hơn mục tiêu trả lời sai.
- **BCE/NLL:** mức sai lệch của xác suất dự đoán; càng thấp thường càng tốt.
- **Brier:** độ lệch bình phương giữa xác suất dự đoán và kết quả thật; càng
  thấp thường càng tốt.

Đây chỉ là kiểm tra mô hình hoạt động bình thường. Không dùng một chênh lệch
AUC nhỏ để xếp hạng mô hình hoặc kết luận về tín hiệu tắt.

### Chênh lệch của phép kiểm tra

Với mỗi mục tiêu:

$$
\Delta_i = p_M(H_i^+) - p_M(H_i^-).
$$

Hiểu đơn giản:

- `plus`: phần lịch sử được thay đổi theo hướng tích cực;
- `minus`: đúng phần lịch sử đó nhưng thay đổi theo hướng tiêu cực;
- chênh lệch dương: mô hình dự đoán xác suất cao hơn ở `plus`;
- chênh lệch gần 0: mô hình ít phản ứng với thay đổi đó.

Các cột chính trong bảng tổng hợp:

| Cột | Ý nghĩa |
| --- | --- |
| `n_pairs` | Số mục tiêu có đủ cả hai phía. |
| `mean_delta` | Chênh lệch trung bình. |
| `median_delta` | Chênh lệch trung vị. |
| `p05_delta`, `p95_delta` | Phạm vi phân bố chênh lệch. |
| `ci_low`, `ci_high` | Khoảng bootstrap của trung bình. |
| `stratum` | Nhóm tỷ lệ nền thấp/giữa/cao hoặc toàn bộ mục tiêu. |

## Đọc từng trường hợp

### IAP-01 — Tỷ lệ đúng nền của câu hỏi

Mở các file:

```text
outputs/predictions_probe/<bo_du_lieu>/<mo_hinh>/seed_<hat_giong>/IAP-01_summary.csv
```

So sánh `mean_delta` giữa các nhóm:

```text
prior_low
prior_middle
prior_high
```

Mẫu hình đáng xem xét sâu hơn khi:

- câu hỏi có đủ số lần xuất hiện;
- số cặp trong các nhóm đủ lớn;
- hướng tác động lặp lại qua các hạt giống;
- cùng câu hỏi, khái niệm và mục tiêu được giữ nguyên;
- chỉ phần trả lời cục bộ được thay đổi;
- độ nhạy với bằng chứng cục bộ giảm ở nhóm tỷ lệ nền cực trị;
- dự đoán tự nhiên có dấu hiệu bị neo gần tỷ lệ nền;
- nhóm đã phân tích khả năng đây chỉ là ảnh hưởng hợp lệ của độ khó câu hỏi.

Không so sánh AUC của toàn bộ test với một nhóm câu hỏi tỷ lệ nền cao để kết
luận. Đó có thể chỉ là khác biệt về độ khó và thành phần nhóm.

### LGT-01 — Xu hướng trả lời chung của người học

Mở:

```text
outputs/predictions_probe/<bo_du_lieu>/<mo_hinh>/seed_<hat_giong>/LGT-01_summary.csv
```

Chênh lệch dương lớn cho thấy mô hình nhạy với phần lịch sử ở các khái niệm
khác trong phép kiểm tra. Chỉ nên xem đây là trường hợp đáng nghiên cứu khi:

- có đủ tương tác ở các khái niệm khác;
- hai phía `plus`/`minus` có thể so sánh công bằng;
- bằng chứng cục bộ, câu hỏi, khái niệm và nhãn mục tiêu được giữ nguyên;
- hướng tác động lặp lại qua hạt giống và tốt nhất là qua bộ dữ liệu khác;
- tác động không được giải thích đầy đủ bởi năng lực chung của người học;
- phần lịch sử thay đổi không quá xa dữ liệu tự nhiên.

## Cách phát biểu kết quả

Nên dùng các mức phát biểu sau:

1. **Hồ sơ nguồn:** tín hiệu tồn tại và có khả năng dự báo trong dữ liệu.
2. **Độ nhạy trong phép kiểm tra:** mô hình phản ứng với tín hiệu khi input được
   thay đổi theo quy tắc đã định.
3. **Mẫu hình có điều kiện:** có dấu hiệu mô hình dựa vào tín hiệu trong điều
   kiện cụ thể, sau khi xem các cách giải thích cạnh tranh.
4. **Đủ cơ sở chuyển CĐ2:** mẫu hình lặp lại, có hiệu chuẩn và có đối chứng phù
   hợp.

Không nên viết “mô hình bị bias” hoặc “bộ dữ liệu có shortcut bias” chỉ từ một
file tổng hợp.

## Các cổng cần xem xét

| Cổng | Câu hỏi cần trả lời |
| --- | --- |
| G0 — Tái lập | Có biết chính xác dữ liệu, cấu hình, hạt giống, phần chia và trạng thái mô hình không? |
| G1 — Khả năng khai thác | Tín hiệu có đủ số liệu, độ phủ và khả năng dự báo không? |
| G2 — Hợp lệ phép kiểm tra | Hai phía có giữ đúng mục tiêu và chỉ thay đổi phần được chỉ định không? |
| G3 — Tín hiệu ứng viên | Chênh lệch có hướng rõ, ổn định và có giải thích cạnh tranh phù hợp không? |
| G4 — Chuyển CĐ2 | Có đủ bằng chứng, đối chứng, giới hạn và khả năng lặp lại không? |

Chương trình chỉ tạo file phục vụ xem xét; nhóm phải tự quyết định đã vượt cổng
hay chưa theo `PLAN.md`.

## Lưu ý quan trọng

- Dùng `uv run`, không dùng `python3` hệ thống để chạy dự án.
- Mô hình phải chạy trên GPU CUDA.
- `test_natural` phải được giữ nguyên.
- Không tính AUC trên phần lịch sử đã bị sửa.
- Nhãn mục tiêu chỉ để kiểm toán, không được đưa vào đầu vào mô hình.
- Không trộn dữ liệu gốc và thông tin mô tả từ các bản tải khác nhau.
- Chạy sàng lọc dài và đối chứng chéo sau khi nhóm đã duyệt kết quả chạy thử.

Đặc tả kỹ thuật, cấu trúc mã, cách tích hợp pyKT và các giới hạn triển khai nằm
trong [`IMPLEMENTATION.md`](IMPLEMENTATION.md).
