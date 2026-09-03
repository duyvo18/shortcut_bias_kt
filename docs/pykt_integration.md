# Ranh giới tích hợp pyKT v0.2

## Phân công

pyKT cung cấp preprocessing, split, loader và model primitives cho DKT/SAINT/AKT.
Dự án giữ ownership đối với raw-event table, mapping all-skill, fold audit,
label-edit IAP, relation index LGT, invariants và reporting.

Repository khóa `pykt-toolkit==0.0.38`. Khi tham khảo mã pyKT mới hơn, phải kiểm
lại API tương thích với phiên bản đã khóa trước khi gọi.

## Dataset trong panel

### Eedi / `nips_task34`

Adapter gọi preprocess Eedi với raw train file và metadata directory, đồng thời
đọc subject metadata để dựng hierarchy relation index. Model forward dùng
`concept_id` primary của pyKT, nhưng LGT giữ toàn bộ `concept_ids` của event.

### `algebra2005`

Adapter gọi preprocess Algebra2005; pyKT tạo item từ:

- item = `Problem Name + Step Name`;
- KC list = `KC(Default)`;
- response = `Correct First Attempt`;
- timestamp = `First Transaction Time`.

Không được thêm `assist2009` vào workflow v0.2.

## Multi-skill và question-level output

pyKT có thể mở rộng/nhân bản interaction nhiều KC để huấn luyện theo concept.
Điều đó không làm các bản sao trở thành raw question-event độc lập. Prior IAP,
local evidence, LGT eligibility và intervention manifest phải tham chiếu raw
event và full KC list; chỉ forward model mới được dùng dòng expanded tương ứng.

## Dataset-specific LGT mode

| Dataset | Mode | Rule |
|---|---|---|
| Eedi | `hierarchy_aware` | Exclude same, ancestor, descendant, sibling, same question và mọi raw event có một skill không đạt |
| Algebra2005 | `exact_unrelated` | Exclude same question và mọi raw event có skill giao target list; không suy luận hierarchy |

Các mode này không được gộp effect size vào cùng một ước lượng.
