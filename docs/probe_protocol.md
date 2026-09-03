# Quy trình can thiệp và kiểm chứng v0.2

Tài liệu này thay thế protocol cặp prefix v0.1. IAP-01 và LGT-01 dùng hai loại
can thiệp khác nhau; không được dùng chung một generator rồi suy diễn rằng chúng
có cùng bất biến.

## 1. Đơn vị dữ liệu và all-skill invariant

Mọi audit bắt đầu từ **raw question-event**. Record phải giữ:

`event_id`, `learner_id`, `question_id`, `concept_ids`, `response`, `timestamp`,
`sequence_id`, `position`, `fold` và dấu hiệu event nhiều skill.

Không được thu gọn `concept_ids` thành một concept đầu tiên khi:

- đếm support/prior item cho IAP;
- xác định local evidence;
- chọn event history cho LGT;
- xác minh invariant sau can thiệp.

Nếu pyKT biểu diễn một event nhiều skill thành nhiều dòng, các dòng đó phải cùng
liên kết tới raw `event_id`. Một response chung không được đổi ở chỉ một bản sao
concept nếu raw event chứa skill khác có quan hệ với target.

## 2. IAP-01: can thiệp train

IAP tạo hai bản train cho từng item treatment `q`:

| Arm | Chỉ thay đổi |
|---|---|
| `prior_high` | Một tập raw train event của `q`: `response 0 → 1` |
| `prior_low` | Một tập raw train event của `q`: `response 1 → 0` |

Cần kiểm trước train:

- arm chỉ khác raw train event được liệt kê trong manifest;
- item/concept list/timestamp/order/length không đổi;
- prior gốc, prior đích và prior đạt được được ghi;
- validation và `test_natural` không bị sửa;
- train event đúng fold được dùng, không lẫn validation.

Cần kiểm trước inference:

- hai arm có cùng danh sách test target;
- hash raw test và hash từng `prefix + target metadata` giống nhau;
- target label chỉ tồn tại ở cột audit, không truyền model.

Artifact tối thiểu: `changed_train_event_ids`, item, arm, seed, fold, prior
gốc/đích/đạt được, số label đổi, hash train/test và checkpoint.

## 3. LGT-01: can thiệp inference

LGT không huấn luyện lại model. Một target của checkpoint tự nhiên có ba prefix
`H0/H+/H-`; chỉ cột response tại cùng tập event hợp lệ được phép khác.

Event history `e` hợp lệ khi different question và all-skill disjoint với target.
Với hierarchy, kiểm mọi cặp source-target skill: same/ancestor/descendant/sibling
đều bị loại. Nếu bất kỳ skill nào không qua luật, loại cả raw event `e`.

Cần kiểm trước forward:

- `H+/H-` có cùng length, order, event IDs, question IDs, concept lists, timestamp;
- target và local evidence hoàn toàn giống nhau;
- `H+` và `H-` đổi đúng cùng `changed_event_ids`;
- mọi ID đổi đều có audit relation `unrelated`;
- mỗi event nhiều skill mang đủ danh sách skill gốc;
- `relation_mode` là `hierarchy_aware` hoặc `exact_unrelated`.

Artifact tối thiểu: target ID, changed IDs, all-skill lists, relation audit, lý
do event bị loại, seed, temporal buffer, predictions `H0/H+/H-`.

## 4. Chỉ số và thống kê

- IAP: $\Delta_{\mathrm{IAP}}=p_{\mathrm{prior\ high}}-p_{\mathrm{prior\ low}}$
  trên cùng target test. CI phải cluster theo item treatment.
- LGT: $\Delta_{\mathrm{LGT}}=p(H+)-p(H-)$ trên cùng checkpoint/target.
- Không tính AUC trên LGT prefix sửa. AUC/NLL/Brier IAP chỉ dùng trên test không
  đổi và là chỉ số phụ.
- Luôn lưu từng prediction pair/arm; không chỉ lưu summary.

## 5. Điều kiện dừng chung

Dừng case-dataset khi raw-event mapping bị mất, treatment không đạt prior đích,
test fingerprint không khớp, LGT không có đủ event all-skill eligible, hoặc can
thiệp tạo thay đổi vượt ngưỡng đã khóa về số event/temporal profile.
