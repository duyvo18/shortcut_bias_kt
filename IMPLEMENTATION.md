# Đặc tả triển khai — thiết kế v0.2

## Trạng thái

Tài liệu này là hợp đồng để nâng code lên thiết kế v0.2 trong [PLAN.md](PLAN.md).
Repository hiện vẫn là **v0.1**:

- IAP đổi local response trong prefix test thay vì label train;
- LGT dùng điều kiện một concept ID khác target;
- canonical data bỏ các skill còn lại của event nhiều skill;
- adapter mới hỗ trợ Eedi và ASSISTments, chưa hỗ trợ Algebra2005.

Vì vậy không được chạy CLI hiện tại như một thực nghiệm v0.2. Không xoá pipeline
v0.1 cho đến khi v0.2 có test thay thế, nhưng không được ghi artifact v0.1 dưới
tên IAP-01/LGT-01 v0.2.

## 1. Phạm vi đã khóa

- Dataset: `nips_task34` và `algebra2005`.
- Model: `dkt`, `saint`, `akt`.
- IAP: label-edit raw train event, tái huấn luyện theo `item × arm × seed × model`.
- LGT: đổi prefix inference của checkpoint tự nhiên, sau all-skill/hierarchy audit.
- Test tự nhiên bất biến trong mọi arm.

pyKT vẫn chịu trách nhiệm preprocess/split/model/training primitives. Dự án này
chịu trách nhiệm raw-event audit, mappings, intervention, invariants, prediction
collection và reporting.

## 2. Hạng mục implementation bắt buộc

### 2.1. Data layer và fold chính xác

Thay canonical table một-concept bằng schema có:

`raw_event_id`, `question_id`, `concept_ids`, `response`, `learner_id`,
`timestamp`, `sequence_id`, `position`, `fold` và mapping raw event ↔ các dòng
pyKT mở rộng. Có thể giữ `model_concept_id` cho forward, nhưng không dùng nó một
mình trong IAP/LGT selection.

Xây đúng phần train của fold từ cùng rule mà `init_dataset4train` dùng. Không
fit prior trên toàn bộ `train_valid_sequences_quelevel.csv`; validation fold và
test phải bị loại.

### 2.2. Adapter dataset

- Giữ adapter Eedi và thêm raw metadata loader: question → all subjects, subject
  → parent/level/path để tạo relation index.
- Thêm adapter Algebra2005 dùng preprocess pyKT, đồng thời giữ raw
  `Problem Name`, `Step Name`, `KC(Default)` và mapping item-step/KC.
- Không thêm ASSIST2009 vào config hoặc workflow v0.2.
- Tạo data audit trước mọi train: item support, 0/1 balance, multi-skill rate,
  target coverage, mapping coverage và relation coverage.

### 2.3. IAP train intervention

Tạo module riêng, ví dụ `train_interventions.py`:

1. chọn item treatment từ raw train audit, không dùng test label;
2. chọn deterministic event IDs cho `prior_high` và `prior_low`;
3. sinh artifact train arm tách biệt, chỉ response ở ID đã chọn khác;
4. tái tạo input pyKT/train loader của arm mà không đụng validation/test;
5. train checkpoint theo `dataset/model/item/arm/seed/fold`;
6. xác minh hash test/prefix/target bằng nhau trước prediction;
7. lưu prior gốc/đích/đạt được cùng manifest.

IAP không gọi `build_iap_pair` v0.1 và không dùng summary `H+/H-` prefix.

### 2.4. LGT relation index và probe

Tạo module relation, ví dụ `concept_relations.py`:

- API trả `same`, `ancestor`, `descendant`, `sibling`, `unrelated` hoặc
  `unknown` cho một cặp skill;
- Eedi bắt buộc relation index từ metadata;
- Algebra2005 chạy `exact_unrelated` nếu chưa có hierarchy;
- event history chỉ eligible khi different question và **mọi** source-target
  skill pair hợp lệ; nếu event nhiều skill có một quan hệ cấm, loại toàn event.

Sửa generator LGT để nhận raw-event mapping, trả về `changed_event_ids` và audit
reason. `H+/H-` phải sửa cùng ID. Validator phải assert mọi cột trừ response tại
các ID đó đều bất biến.

### 2.5. Prediction, metrics và artifact

- Prediction collector phải hỗ trợ arm/checkpoint IAP và model tự nhiên LGT.
- IAP output có item, arm, seed, prior information, target/local strata và test
  fingerprint; CI/bootstrap cluster theo item trước target.
- LGT output có all-skill source/target audit, relation mode, IDs đổi, seed,
  temporal buffer và `H0/H+/H-` predictions.
- Tạo và ghi `item_only`, `local_only`, `global_only` source controls.
- Không dùng AUC trên prefix LGT sửa; metric IAP tính trên test bất biến và là phụ.

## 3. Cấu trúc artifact đích

    outputs/
      data_audits/<dataset>/
      train_interventions/<dataset>/<item>/<arm>/manifest.json
      checkpoints/<dataset>/<model>/<item-or-natural>/<arm>/seed_<seed>/
      predictions_natural/<dataset>/<model>/seed_<seed>.csv
      predictions_iap/<dataset>/<model>/<item>/seed_<seed>.csv
      predictions_lgt/<dataset>/<model>/seed_<seed>.csv
      summaries/<dataset>/<model>/IAP-01_*.csv
      summaries/<dataset>/<model>/LGT-01_*.csv

## 4. Test bắt buộc trước smoke

1. Unit test IAP: chỉ các raw train IDs được liệt kê đổi response; prior đạt giá
   trị đã ghi; validation/test hash giữ nguyên.
2. Unit test multi-skill: history event bị từ chối khi **một** skill same hoặc
   related target.
3. Unit test hierarchy Eedi: same/ancestor/descendant/sibling bị loại,
   unrelated được giữ.
4. Unit test Algebra2005: only different question + all-skill disjointness được
   chọn và output mang `exact_unrelated`.
5. Integration test fold: prior/source profile dùng đúng train partition.
6. Integration test prediction: hai IAP arm nhận cùng test fingerprint; LGT
   target/local evidence bất biến và `H+/H-` đổi cùng IDs.
7. Smoke GPU: DKT/SAINT/AKT train/load/predict được cho một item/arm nhỏ.

## 5. Môi trường

Dependency vẫn khóa tại `pykt-toolkit==0.0.38`, Python 3.11 và CUDA bắt buộc.
Không sửa tay `pyproject.toml`; nếu cần dependency mới dùng `uv add`. Cấu hình
CPU/GPU và lệnh kiểm tra môi trường hiện có vẫn áp dụng, nhưng config hiện hành
là config v0.1 và chưa đủ để chạy v0.2.
