# Thí điểm shortcut bias trong Knowledge Tracing

## Trạng thái

Code hiện triển khai thiết kế thực nghiệm **v0.2**. IAP là label-edit ở train;
LGT là can thiệp inference sau all-skill relation audit.

Mục tiêu là kiểm tra độ nhạy của model trong can thiệp đã khóa; một effect không
tự động chứng minh dataset/model có shortcut bias. Độ khó item và năng lực chung
của learner có thể là thông tin hợp lệ.

## Panel đã chốt

- Dataset: `nips_task34` (Eedi) là chính; `algebra2005` là đối chứng chính.
  `assist2009` không thuộc panel.
- Model: DKT, SAINT và AKT; không thêm deep baseline ở vòng này.
- Dataset và feasibility gate: [docs/dataset_panel.md](docs/dataset_panel.md).

## Hai case

### IAP-01 — can thiệp ở train

Với một item `q`, tạo hai train arm bằng label-edit chỉ ở event train của `q`:
`prior_high` đổi một số response `0 → 1`; `prior_low` đổi một số response
`1 → 0`. Mỗi arm huấn luyện model riêng, rồi dự đoán trên **cùng test prefix và
target bất biến**.

Chỉ số chính:

$$
\Delta_{\mathrm{IAP}} =
p_{\mathrm{prior\ high}}(H^{test},q)-
p_{\mathrm{prior\ low}}(H^{test},q).
$$

Đọc thêm: [case card IAP-01](case_cards/IAP-01.md).

### LGT-01 — can thiệp ở inference

Với cùng checkpoint và target, giữ nguyên local evidence, rồi đổi response ở
cùng các event history đủ điều kiện sang toàn đúng/toàn sai. Event chỉ đủ điều
kiện nếu khác target question, không giao **toàn bộ** skill target, và — nếu
dataset có hierarchy — không same/ancestor/descendant/sibling với bất kỳ target
skill nào. Một event nhiều skill có một skill liên hệ là bị loại toàn bộ.

Chỉ số chính:

$$
\Delta_{\mathrm{LGT}}=p_M(H^+,q)-p_M(H^-,q).
$$

Eedi báo cáo `hierarchy_aware`; Algebra2005 báo cáo `exact_unrelated` cho đến
khi có taxonomy được xác minh. Đọc thêm: [case card LGT-01](case_cards/LGT-01.md).

## Tài liệu

| Cần biết | Xem |
|---|---|
| Thiết kế, cổng và artifact | [PLAN.md](PLAN.md) |
| Quyết định Eedi + Algebra2005 | [docs/dataset_panel.md](docs/dataset_panel.md) |
| Bất biến và audit | [docs/probe_protocol.md](docs/probe_protocol.md) |
| Hạng mục code cần làm | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| Ranh giới pyKT/dataset | [docs/pykt_integration.md](docs/pykt_integration.md) |

## Điều không được vi phạm

- Không sửa test, prefix test, target metadata hoặc dùng target label làm input.
- Không tính item prior trên sequence pyKT đã nhân bản multi-skill.
- Không giảm `concept_ids` xuống một skill khi chọn history LGT.
- Không tính AUC trên LGT prefix bị sửa.
- Không gộp trực tiếp LGT effect của Eedi và Algebra2005 vì relation mode khác nhau.
