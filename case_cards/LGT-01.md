# LGT-01 — Xu hướng trả lời chung của người học ở khái niệm mới hoặc thưa

## 1. Mục đích

Kiểm tra xem khi bằng chứng trực tiếp về khái niệm đích còn ít, mô hình có bị
kéo mạnh bởi việc người học thường trả lời đúng/sai ở các khái niệm khác hay không.

## 2. Tín hiệu được kiểm tra

Với mục tiêu $(u,t,c)$, tính trung bình câu trả lời trước mục tiêu ở ngoài khái niệm $c$:

$$
G_{u,t,c}=\operatorname{mean}\{R_j:j<t, C_j\ne c\}.
$$

Đây là hồ sơ cho biết tín hiệu có thể được khai thác, không mặc nhiên là thông
tin sai. Nó có thể phản ánh năng lực chung của người học.

## 3. Đối tượng đủ điều kiện

Mục tiêu kiểm tra phải có ít hơn `local_min_support` tương tác trực tiếp với
khái niệm đích, hoặc chưa từng gặp khái niệm đó, đồng thời có ít nhất
`remote_min_support` tương tác ở khái niệm khác.

## 4. Bằng chứng cần giữ

Giữ nguyên câu hỏi mục tiêu, khái niệm mục tiêu, đoạn lịch sử cục bộ, nhãn mục
tiêu, thứ tự sự kiện, thời điểm và độ dài phần lịch sử. Giải thích cạnh tranh
quan trọng nhất là năng lực chung thực sự có thể giúp dự đoán ở khái niệm mới.

## 5. Cách tạo cặp kiểm tra

- `H0`: phần lịch sử tự nhiên;
- `H+`: đổi câu trả lời ở đoạn xa được chọn sang hướng đúng;
- `H-`: đổi đúng các vị trí đó sang hướng sai.

Lịch sử cục bộ và mục tiêu không thay đổi. Các câu trả lời đã sửa chỉ là đầu vào
đối chứng, không được coi là nhãn học tập thật.

## 6. Chỉ số

Với mục tiêu $i$:

$$
\Delta_{global}^{(i)} = p_M(H_{global+}^{(i)},q_i) - p_M(H_{global-}^{(i)},q_i).
$$

Báo cáo phân bố chênh lệch, trung bình, trung vị, khoảng bootstrap, số lượng
quan sát, độ cân bằng giữa hai phía và mức khác dữ liệu.

## 7. Cách diễn giải

Chênh lệch lớn cho thấy mô hình nhạy với hồ sơ trả lời ở các khái niệm khác
trong phép kiểm tra. Chỉ nên coi đó là dấu hiệu đáng nghiên cứu khi tác động vẫn
rõ sau khi xem số lượng quan sát, mức chồng lấp, hạt giống, bộ dữ liệu khác và
giải thích bằng năng lực chung.

Không được gọi kết quả này là thiên lệch của bộ dữ liệu hoặc bằng chứng nhân quả.
