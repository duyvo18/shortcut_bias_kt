# LGT-01 — Xu hướng trả lời chung từ lịch sử không liên hệ tại inference

## 1. Mục đích

Kiểm tra ở **giai đoạn inference**: trong cùng một checkpoint, với target và
local evidence được giữ nguyên, việc đổi response của những event lịch sử thật
sự không liên hệ với target concept có làm thay đổi dự đoán hay không.

Đây là phép kiểm tra mức độ model nhạy với learner-global trend. Năng lực chung
có thể là bằng chứng hợp lệ, đặc biệt khi target concept mới/thưa.

## 2. Target và local evidence giữ nguyên

Target đủ điều kiện có target concept mới/thưa theo ngưỡng `n_local` đã khóa và
có đủ event lịch sử đủ điều kiện để đổi. Local evidence là các event trước target
có giao với **toàn bộ** `concept_ids` của target; nó cùng target, question,
timestamp, response audit và độ dài prefix phải bất biến trong `H0/H+/H-`.

Nếu target item hiếm nhưng target concept đã có nhiều history qua item khác,
không được gọi nó là trường hợp local evidence thưa chỉ dựa vào `n_item`.

## 3. Luật chọn event lịch sử có thể đổi

Với history event `e` và target `i`, chỉ cho phép đổi `e` khi mọi điều kiện sau
đúng:

1. `question_id(e) != question_id(i)`;
2. `concept_ids(e)` không giao `concept_ids(i)`;
3. nếu có hierarchy đã xác minh, mọi cặp skill giữa `concept_ids(e)` và
   `concept_ids(i)` đều là `unrelated`: không same, ancestor, descendant hay
   sibling;
4. nếu không có hierarchy đã xác minh, gắn `relation_mode=exact_unrelated` và
   chỉ chấp nhận all-skill disjointness;
5. với event nhiều skill, **một** skill cùng/liên hệ gần target là đủ để loại
   toàn bộ event; không được chỉ bỏ skill đó rồi đổi response chung của event.

Eedi phải chạy `hierarchy_aware`. Algebra2005 chỉ được báo cáo
`exact_unrelated` cho đến khi có taxonomy KC được xác minh. Các event cùng target
question luôn bị loại, kể cả khi mapping concept khác.

## 4. Cặp inference đối chứng

- `H0`: prefix test tự nhiên;
- `H+`: đặt response của đúng các `changed_event_ids` đủ điều kiện thành 1;
- `H-`: đặt response của đúng các ID đó thành 0.

Hai phía dùng cùng checkpoint, target, vị trí, question IDs, **all-skill lists**,
timestamps, độ dài prefix và seed chọn vị trí. Có thể đặt temporal buffer trước
target, nhưng phải đăng ký trong config. `G_eligible` là trung bình response
trên tập event đủ điều kiện được dùng cho case, không phải toàn bộ non-target
history.

## 5. Chỉ số

$$
\Delta_{\mathrm{LGT}}^{(i)}
=\hat p_M(H_i^+,q_i)-\hat p_M(H_i^-,q_i).
$$

Báo cáo phân bố, bootstrap CI, số pair, số event đổi, `relation_mode`, tỷ lệ
event bị loại theo lý do hierarchy/multi-skill và độ khác so với history tự
nhiên. Không tính AUC trên prefix đã sửa.

## 6. Diễn giải

$\Delta_{\mathrm{LGT}}$ lớn cho thấy model nhạy với learner-global trend trong
history được xác nhận không liên hệ theo luật đang dùng. Nó chỉ là candidate
shortcut khi tác động quá mạnh so với local evidence, gây overconfidence hoặc
đi ngược dấu local evidence, và lặp lại qua seed/dataset.

Không gọi learner-global trend là nhiễu hoặc bias chỉ vì nó có tác động; đó có
thể là năng lực tổng quát hợp lệ.
