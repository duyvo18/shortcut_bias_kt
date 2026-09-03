# Panel dữ liệu v0.2

## Quyết định

Thí điểm dùng hai dataset lõi:

| Dataset | Vai trò | IAP-01 | LGT-01 |
|---|---|---|---|
| `nips_task34` | Chính | label-edit theo `QuestionId` | `hierarchy_aware` từ Eedi subject metadata |
| `algebra2005` | Đối chứng chính | label-edit theo `Problem Name + Step Name` | `exact_unrelated` cho đến khi có taxonomy được xác minh |

`assist2009` không nằm trong panel. Skill Builder có quy tắc mastery/dừng sau ba câu đúng liên tiếp; đó là một cơ chế chọn dữ liệu có thể làm nhiễu item prior và learner-global trend. Một record cũng có thể mang nhiều skill. Dataset không được thêm lại chỉ để tăng số benchmark.

## Eedi / `nips_task34`

Eedi có interaction câu hỏi–người học ở quy mô lớn và metadata câu hỏi/subject. Tiền xử lý pyKT đọc `question_metadata_task_3_4.csv` và `subject_metadata.csv`, đồng thời dùng `Level` để chọn subject; dự án phải đọc metadata gốc để giữ full hierarchy thay vì chỉ giữ level 3 mà pyKT dùng cho model. Đây là dataset duy nhất của panel có thể báo cáo LGT là `hierarchy_aware`.

Nguồn: [Diagnostic Questions challenge guide](https://arxiv.org/abs/2007.12061), [pyKT Eedi preprocessing](https://pykt.org/pykt-team.github.io_old/docs/_modules/pykt/preprocess/nips_task34_preprocess.html).

## Algebra2005

pyKT định danh item bằng `Problem Name + Step Name`, dùng `KC(Default)`, `Correct First Attempt` và timestamp. Cấu trúc item-step này là đối chứng tốt cho Eedi trong IAP, nhưng pipeline chuẩn không cung cấp taxonomy KC đủ để loại sibling/ancestor/descendant trong LGT. Vì vậy rule LGT bảo thủ là all-skill disjointness và different question; output luôn mang `relation_mode` là `exact_unrelated`.

Nguồn: [pyKT Algebra2005 preprocessing](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/preprocess/algebra2005_preprocess.py), [Knowledge Tracing survey](https://doi.org/10.1145/3569576).

## Feasibility gate trước huấn luyện

Trên raw event của **train split đúng fold**, không phải sequence pyKT đã mở rộng multi-skill, phải lưu:

- số event, learner, item, concept và tỷ lệ multi-skill;
- với mỗi item: `n_q`, số response 0/1, prior gốc và mức prior high/low đạt được với ngân sách label-edit;
- số target test từng item; target selection không dùng test label;
- tỷ lệ event history đủ điều kiện LGT sau khi xét **tất cả** source skill;
- với Eedi: số event bị loại vì same/ancestor/descendant/sibling và hierarchy coverage; với Algebra2005: xác nhận `exact_unrelated`.

Không chạy case-dataset nếu gate không đạt ngưỡng đã khóa.
