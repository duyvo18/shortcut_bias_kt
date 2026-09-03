# Quy trình tạo phép kiểm tra đối chứng

Tài liệu này giải thích cách tạo các cặp dữ liệu đối chứng theo `PLAN.md`. Phép
kiểm tra đối chứng là một thay đổi có chủ đích trên đầu vào, không phải một bộ
dữ liệu đánh giá mới.

## 1. Bảng dữ liệu chuẩn

Mỗi dòng biểu diễn một sự kiện tương tác và có các trường:

`sequence_id`, `position`, `event_id`, `learner_id`, `question_id`,
`concept_id`, `response`, `timestamp` và `fold`. Đây là tên trường do chương
trình sử dụng; không cần thay đổi khi chỉnh sửa tài liệu hay dữ liệu.

Nhãn mục tiêu được lưu riêng dưới `target_label` chỉ để kiểm toán. Không bao giờ
đưa nhãn này vào đầu vào của mô hình.

## 2. Nguyên tắc bất biến trong một cặp

Mỗi mục tiêu tạo ba phiên bản:

- `natural`: phần lịch sử tự nhiên;
- `plus`: phiên bản thay đổi theo hướng tích cực;
- `minus`: phiên bản thay đổi theo hướng tiêu cực.

Giữa `plus` và `minus` phải giữ nguyên:

- câu hỏi và khái niệm của mục tiêu;
- nhãn mục tiêu và định danh sự kiện;
- độ dài và thứ tự phần lịch sử;
- câu hỏi/khái niệm/thời điểm trong phần lịch sử;
- mọi vị trí không được trường hợp kiểm tra chỉ định thay đổi.

Chỉ câu trả lời tại các vị trí đã chọn mới được thay đổi. Dự đoán chỉ lấy tại
mục tiêu được bảo vệ, không dùng câu trả lời đã sửa làm nhãn tuần tự mới.

## 3. Chỉ số

Với target $i$:

$$
\Delta_i = p_M(H_i^+) - p_M(H_i^-).
$$

Giữ lại từng dòng dự đoán để xem mục tiêu bất thường. Bảng tổng hợp gồm trung
bình, trung vị, phân vị 5%/95% và khoảng bootstrap.

## 4. Điều kiện dừng

Không chạy phép kiểm tra nếu nguồn quá ít, không có phần dữ liệu chồng lấp,
không đủ cặp hoặc hồ sơ sau biến đổi quá khác dữ liệu tự nhiên. Các ngưỡng phải
nằm trong YAML và được khóa mà không nhìn nhãn kiểm tra.
