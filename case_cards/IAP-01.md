# IAP-01 — Tỷ lệ đúng nền của câu hỏi có thể che mờ bằng chứng cục bộ

## 1. Mục đích

Kiểm tra xem mô hình còn phản ứng với lịch sử gần đây của người học ở đúng
khái niệm cần dự đoán hay không, đặc biệt khi câu hỏi đích vốn thường được trả
lời đúng hoặc sai trong tập huấn luyện.

## 2. Tín hiệu được kiểm tra

Với câu hỏi $q$, tính tỷ lệ đúng nền từ tập huấn luyện:

$$
\hat{\pi}_q = \frac{\sum R_t}{\#\{t: Q_t=q\}}.
$$

Chỉ dùng câu hỏi có ít nhất `item_min_support` quan sát. Nhóm tỷ lệ nền thấp,
giữa và cao được chia bằng các mốc tính từ tập huấn luyện, không nhìn nhãn kiểm
tra để đặt mốc.

## 3. Đối tượng đủ điều kiện

Một mục tiêu kiểm tra phải có:

- câu hỏi và khái niệm đích xác định được;
- ít nhất `local_min_support` tương tác trước đó với khái niệm đích;
- nhãn mục tiêu được lưu để kiểm toán nhưng không đưa vào đầu vào mô hình.

## 4. Bằng chứng cần giữ

Giữ nguyên câu hỏi mục tiêu, khái niệm mục tiêu, nhãn mục tiêu, thứ tự sự kiện,
độ dài phần lịch sử và thông tin ở các khái niệm khác. Bằng chứng cần quan sát là
các câu trả lời gần đây của người học trên khái niệm đích.

## 5. Cách tạo cặp kiểm tra

- `H0`: phần lịch sử tự nhiên, dùng để tham chiếu;
- `H+`: đổi câu trả lời tại cùng các vị trí cục bộ sang hướng đúng;
- `H-`: đổi đúng các vị trí đó sang hướng sai.

Không thay đổi mục tiêu hoặc các trường câu hỏi/khái niệm/thời điểm. Chỉ đọc
xác suất tại mục tiêu đã khóa; không tính AUC trên phần lịch sử đã bị sửa.

## 6. Chỉ số

Với mục tiêu $i$:

$$
\Delta_{local}^{(i)} = p_M(H_{local+}^{(i)},q_i) - p_M(H_{local-}^{(i)},q_i).
$$

Báo cáo phân bố chênh lệch, trung bình, trung vị, các phân vị và khoảng bootstrap
theo `prior_low`, `prior_middle`, `prior_high`.

## 7. Cách diễn giải

Chênh lệch cho thấy mô hình nhạy với thay đổi cục bộ trong phép kiểm tra này.
Một mẫu hình đáng xem xét sâu hơn là độ nhạy cục bộ giảm rõ ở nhóm tỷ lệ nền
cực trị, dự đoán tự nhiên có xu hướng gần tỷ lệ nền và mẫu hình lặp lại qua các
hạt giống.

Đây chưa phải bằng chứng mô hình bị thiên lệch tín hiệu tắt. Độ khó câu hỏi có
thể vẫn là thông tin hợp lệ. Báo cáo phải kèm số lượng quan sát, mức chồng lấp,
độ khác dữ liệu, hạt giống và giải thích cạnh tranh.
