# IAP-01 — Can thiệp tỷ lệ đúng nền của item trong train

## 1. Mục đích

Kiểm tra ở **giai đoạn train**: với cùng item target `q` và cùng bằng chứng lịch
sử ở test, việc làm cho `q` có tỷ lệ phản hồi đúng cao/thấp hơn trong train có
làm thay đổi dự đoán test hay không.

Đây là phép kiểm tra về mức độ model học/nhạy với item-answer prior. Nó không
mặc định chứng minh rằng item difficulty là tín hiệu không hợp lệ.

## 2. Tín hiệu và đơn vị can thiệp

Với item `q`, prior gốc tính trên raw event của train split đúng fold:

$$
\hat\pi_q=\frac{\sum_{Q_t=q}R_t}{\#\{t:Q_t=q\}}.
$$

Đơn vị support là **raw question-event**, không phải dòng đã được pyKT nhân bản
do multi-skill. Chỉ chọn item có đủ support, đủ nhãn 0/1, đạt được hai mức prior
đích bằng ngân sách label-edit đã khóa, và có target test; nhãn test không được
dùng để chọn item.

## 3. Hai train arm

Từ cùng một train split, cùng fold và cùng chuỗi event:

- `prior_high`: chỉ chọn các event có `question_id=q` và đổi `response: 0 → 1`;
- `prior_low`: chỉ chọn các event có `question_id=q` và đổi `response: 1 → 0`.

Không đổi learner, item, **toàn bộ** `concept_ids`, vị trí, timestamp, độ dài
chuỗi hoặc bất cứ event nào khác. Phải lưu prior gốc, prior đích, prior đạt được,
danh sách `changed_train_event_ids`, seed chọn event và số nhãn đổi.

Đây là can thiệp nhãn train bán tổng hợp. Vì response train cũng có thể là input
của các bước train sau, IAP đo ảnh hưởng của một training response process khác
cho `q`; không được diễn giải như đã thay đổi độ khó thật của item.

## 4. Những gì phải bất biến ở test

Mỗi arm train một checkpoint riêng với cùng model, fold, seed, initialization,
batch/order policy và siêu tham số. Cả hai checkpoint nhận chính xác cùng:

- raw `test_natural`;
- prefix test của từng target;
- target `event_id`, `question_id`, `concept_ids`, timestamp và nhãn audit.

Nhãn target test không bao giờ là input. Lưu fingerprint/hash của test, prefix
và danh sách target để kiểm tra arm không vô tình dùng test khác nhau.

## 5. Chỉ số

Với target test `i` của item `q`, model `M` và seed `s`:

$$
\Delta_{\mathrm{IAP}}^{(q,i,s)}
=\hat p_{\theta_{q,+,s}}(H_i^{test},q)
-\hat p_{\theta_{q,-,s}}(H_i^{test},q).
$$

Báo cáo theo item, seed và strata local evidence test:

- `n_local = 0`;
- `n_local = 1–2`;
- `n_local >= 3`.

Giữ cụm item khi bootstrap/resample rồi mới resample target trong item. NLL,
Brier và AUC trên các target `q` của test bất biến là chỉ số phụ, không thay
thế phân bố $\Delta_{\mathrm{IAP}}$.

## 6. Diễn giải

Dịch chuyển dự đoán cùng chiều với prior train cho thấy model nhạy với item
prior được tạo trong train trong khi bằng chứng test giữ nguyên. Dấu hiệu
shortcut mạnh hơn chỉ xuất hiện khi hiệu ứng:

- vẫn rõ khi local evidence đủ;
- kéo dự đoán theo hướng không tương xứng hoặc mâu thuẫn với local evidence;
- lặp lại qua item, seed và Eedi/Algebra2005.

DKT là contrast concept-centric, không phải negative control tuyệt đối: effect
mạnh ở DKT có thể cho thấy label-edit đã thay đổi signal chung theo concept hoặc
trajectory train. SAINT và AKT là các model item-aware chính.

## 7. Điều kiện dừng

Không chạy IAP cho item/dataset nếu không thể khóa prior đích với số label-edit
vừa phải, item không đủ 0/1 support, target test quá ít, train fold không khớp
với fold model, hoặc fingerprint test khác nhau giữa hai arm.
