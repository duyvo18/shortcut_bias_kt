# KẾ HOẠCH — Thí điểm kiểm tra sơ khảo các tín hiệu tắt trong truy vết tri thức

**Trạng thái:** thiết kế và implementation v0.2 đã sẵn sàng; cần qua feasibility
gate dữ liệu trước workload huấn luyện đầy đủ.
**Cập nhật:** 03/09/2026
**Phạm vi:** Chuyên đề 1 (CĐ1), kiểm định sơ khảo; không phải benchmark công bố hay thực nghiệm kết luận của luận án.

## 1. Bối cảnh, mục tiêu và giới hạn phát biểu

*Shortcut bias* trong thí điểm này là khả năng mô hình KT dựa quá mức vào một quy luật thống kê dễ khai thác thay vì bằng chứng phù hợp để suy luận trạng thái tri thức của người học. Thí điểm kiểm tra **độ nhạy trong các can thiệp đã định nghĩa**, không chứng minh trực tiếp sự thật nhân quả về năng lực hay quá trình học.

Hai trường hợp làm việc ở hai thời điểm khác nhau trong pipeline:

| Trường hợp | Thời điểm can thiệp | Câu hỏi thí điểm |
|---|---|---|
| IAP-01 | Train | Khi giữ nguyên toàn bộ target và lịch sử test, việc thay đổi tỷ lệ đúng nền của item `q` trong train có làm thay đổi dự đoán test cho `q` không? |
| LGT-01 | Inference | Khi giữ nguyên model, target và bằng chứng local, việc đổi các phản hồi lịch sử thật sự không liên hệ với target concept có làm thay đổi dự đoán không? |

| Mức bằng chứng | Có thể nói gì | Không được nói gì |
|---|---|---|
| Can thiệp IAP/LGT | Model nhạy với tín hiệu ứng viên trong điều kiện đã khóa | Model chắc chắn đã dùng shortcut trong mọi dữ liệu thật |
| Mẫu hình có điều kiện | Có dấu hiệu tín hiệu lấn át/không tương xứng với local evidence | Sự thật nhân quả về năng lực, độ khó, hay học tập |
| Lặp lại, kiểm soát và hiệu chuẩn | Trường hợp đủ mạnh để chuyển CĐ2 | Dữ liệu hoặc mô hình “có bias” một cách tổng quát |

Độ khó item và năng lực chung của learner có thể là bằng chứng hợp lệ. Một chênh lệch chỉ trở thành dấu hiệu shortcut đáng nghiên cứu khi nó bền, có hướng, và lấn át hoặc mâu thuẫn với bằng chứng trạng thái tri thức cần dùng.

## 2. Nguyên tắc thiết kế đã khóa

1. **Test gốc bất biến.** Trong cả hai case, `test_natural`, target, prefix test, câu hỏi, danh sách concept, timestamp và nhãn test dùng để audit phải giống hệt giữa các điều kiện. Nhãn target không bao giờ là input.
2. **Đơn vị dữ liệu là raw question-event.** Support item và prior IAP tính trên event gốc, trước mọi bước nhân bản/mở rộng multi-skill của pyKT.
3. **Giữ toàn bộ danh sách skill.** Mỗi event có `concept_ids` là tập đầy đủ các skill/KC. Không được suy luận quan hệ LGT từ một `concept_id` đầu tiên.
4. **Tách hai loại can thiệp.** IAP tạo hai tập train bán tổng hợp và huấn luyện lại; LGT chỉ sửa một số response trong prefix inference của cùng checkpoint.
5. **Không nhìn nhãn test để chọn treatment.** Item, mức prior đích, event train được sửa, ngưỡng support và luật LGT được khóa trước khi đọc kết quả test.
6. **Không tính AUC trên prefix đã sửa.** Với LGT chỉ đọc dự đoán tại target được bảo vệ. Với IAP, AUC/NLL/Brier trên test bất biến chỉ là chỉ số phụ; thay đổi xác suất tại target là chỉ số chính.
7. **So sánh đối xứng và tái lập.** Hai arm dùng cùng kiến trúc, seed, ngân sách huấn luyện và thứ tự event; mọi ID event thay đổi, seed và fingerprint phải được lưu.

## 3. Panel dữ liệu và baseline

### 3.1. Dataset đã chọn

| Vai trò | Dataset | IAP-01 | LGT-01 | Quyết định |
|---|---|---|---|---|
| Chính | `nips_task34` (Eedi/NeurIPS 2020) | Item support lớn; có `question_id` | `hierarchy_aware`; dùng subject metadata | Chạy đầu tiên |
| Đối chứng chính | `algebra2005` | Item là `Problem Name + Step Name` | `exact_unrelated` nếu không xác minh được hierarchy | Chạy sau khi Eedi qua G0–G2 |
| Không thuộc panel | `assist2009` | Không chạy | Không chạy | Loại khỏi thiết kế v0.2 |

`assist2009` bị loại vì cơ chế Skill Builder/mastery và việc một response có thể được biểu diễn qua nhiều skill làm nhiễu mạnh phép giải thích IAP/LGT. Không được đưa nó trở lại chỉ vì là benchmark phổ biến. Lý do, metadata cần thiết và feasibility gate của hai dataset đã chọn nằm trong [`docs/dataset_panel.md`](docs/dataset_panel.md).

### 3.2. Baseline giữ nguyên

| Mô hình | Vai trò |
|---|---|
| DKT | Đối chứng concept-centric; IAP effect mạnh ở đây cảnh báo label-edit đã dịch chuyển tín hiệu chung theo concept/chuỗi, không thuần item-specific |
| SAINT | Mô hình attention nhận question và concept; đại diện cho việc học association item–history linh hoạt |
| AKT | Mô hình attention có question/concept và question-difficulty variation; là trường hợp item-aware quan trọng nhất cho IAP |

Không thêm deep baseline ở v0.2. Các control không phải KT baseline bắt buộc là `item_only(q)`, `local_only(u,t,c)` và `global_only(u,t,c)`. Chúng kiểm tra treatment/source profile, không được dùng để kết luận shortcut.

### 3.3. Phạm vi chạy

| Giai đoạn | Dataset | Mô hình | Lặp | Mục tiêu |
|---|---|---|---|---|
| Feasibility/smoke | Eedi | DKT, SAINT, AKT | 1 seed | Kiểm dữ liệu, multi-skill, arm IAP và invariant LGT |
| Sàng lọc | Eedi | DKT, SAINT, AKT | 3 seed | Ước lượng hiệu ứng và độ dao động |
| Đối chứng chéo | Algebra2005 | DKT, SAINT, AKT | 3 seed | Kiểm tra tính lặp lại qua môi trường ITS khác |

IAP đòi hỏi tái huấn luyện theo item nên số item treatment phải bị giới hạn bằng ngân sách đã đăng ký trước. Không gộp effect size của Eedi với Algebra2005; đặc biệt LGT có `relation_mode` khác nhau.

## 4. Dữ liệu chuẩn và hồ sơ nguồn

Mỗi raw question-event phải giữ tối thiểu:

`event_id`, `learner_id`, `sequence_id`, `position`, `question_id`, `concept_ids`, `response`, `timestamp`, `fold`, `is_multi_skill`.

Một target model có thể sử dụng một concept được pyKT mở rộng, nhưng mọi luật chọn event và quan hệ của LGT phải truy ngược về raw event cùng **toàn bộ** `concept_ids`. Nếu có nhiều concept ở target, closure cần loại trừ là hợp của mọi concept target.

### 4.1. Item-answer prior cho IAP

Với item `q`, tính trên raw train event của đúng fold:

$$
\hat\pi_q=\frac{\sum_{(u,t)\in\mathrm{train}:Q_t=q}R_t}{\#\{(u,t)\in\mathrm{train}:Q_t=q\}}.
$$

Audit phải ghi `n_q`, số 0, số 1, prior gốc, số target test của `q`, và mức dịch prior khả thi mà không vượt ngân sách label-edit. Chỉ item có đủ cả hai nhãn và đủ target test mới là ứng viên; việc test có target `q` được phép dùng cho coverage nhưng không được dùng nhãn test.

### 4.2. Local evidence

Với target `(u,t,q,C^*)`, local evidence là history trước `t` có giao với `C^*`, trong đó `C^*` là toàn bộ concept của target. Ghi `n_local`, phản hồi gần đây, recency và riêng `n_item` cho cùng `q`. IAP không thay đổi local evidence test; kết quả được báo cáo theo strata `n_local = 0`, `1–2`, `>=3`.

### 4.3. Learner-global trend hợp lệ cho LGT

`G_eligible` chỉ tính trên event lịch sử đủ điều kiện được đổi, không phải mọi event có một concept ID khác target. Với event lịch sử `e` và target `i`, `e` đủ điều kiện khi:

1. `question_id(e) != question_id(i)`;
2. `concept_ids(e)` không giao `concept_ids(i)`;
3. nếu dataset có hierarchy, mọi cặp history-target đều là `unrelated`: không same, ancestor, descendant hay sibling trong taxonomy đã khóa;
4. nếu không có hierarchy đã xác minh, trạng thái được ghi `relation_mode=exact_unrelated`, không được suy luận về sibling;
5. nếu event có nhiều skill, chỉ một skill không đạt điều kiện cũng loại **toàn bộ event** khỏi tập có thể đổi.

Eedi bắt buộc dùng `hierarchy_aware`; Algebra2005 chỉ dùng `exact_unrelated` cho đến khi một taxonomy đáng tin được tích hợp. Có thể đặt minimum temporal lag, nhưng giá trị phải nằm trong cấu hình đã khóa.

## 5. Case IAP-01 — can thiệp label ở train

### 5.1. Mục tiêu và can thiệp

Với mỗi item treatment `q`, tạo hai train arm từ cùng raw train của fold:

- `prior_high`: chỉ đổi một tập event của `q` từ `0 → 1` để đạt $\tilde\pi_q^+$;
- `prior_low`: chỉ đổi một tập event của `q` từ `1 → 0` để đạt $\tilde\pi_q^-$.

Giữ nguyên learner, item, concept list, vị trí, timestamp, độ dài chuỗi và mọi event khác. Đây là **can thiệp nhãn train bán tổng hợp**, không phải thay đổi độ khó thật của item. Vì response train cũng có thể là input của các bước sau, IAP đo ảnh hưởng của một training response process khác cho `q`, không chỉ một intercept tĩnh.

Mỗi `(q, arm, seed, model)` huấn luyện checkpoint riêng nhưng có cùng seed, initialization, batch/order policy, siêu tham số và fold. `test_natural` không thay đổi. Phải lưu hash của raw test/prefix/target để chứng minh hai arm nhận đúng cùng input test.

### 5.2. Chỉ số và diễn giải

Với target test `i` của item `q` và seed `s`:

$$
\Delta_{\mathrm{IAP}}^{(q,i,s)}=\hat p_{\theta_{q,+,s}}(H_i^{\mathrm{test}},q)-\hat p_{\theta_{q,-,s}}(H_i^{\mathrm{test}},q).
$$

Chỉ số chính là phân bố và trung bình có điều kiện của $\Delta_{\mathrm{IAP}}$ theo item, seed và strata local evidence. Resample/CI phải giữ cụm item rồi target, không coi toàn bộ target của cùng `q` là độc lập. NLL/Brier/AUC trên test bất biến của các target `q` chỉ là kiểm tra phụ.

Hiệu ứng cùng chiều cho thấy model nhạy với prior được tạo cho item trong train. Dấu hiệu mạnh hơn về shortcut chỉ xuất hiện khi dịch prior vẫn kéo dự đoán theo hướng không tương xứng hoặc mâu thuẫn với local evidence test, và lặp lại qua item/seed/dataset. Không được dùng IAP effect đơn lẻ để gọi item difficulty là không hợp lệ.

## 6. Case LGT-01 — can thiệp prefix ở inference

### 6.1. Mục tiêu và cặp đối chứng

Mục tiêu là target có target concept mới/thưa (`n_local` dưới ngưỡng đã khóa) và có đủ event lịch sử `G_eligible`. Cùng một checkpoint và một target tạo:

- `H0`: prefix tự nhiên;
- `H+`: đặt response của đúng các `changed_event_ids` đủ điều kiện thành 1;
- `H-`: đặt response của đúng các ID đó thành 0.

Target, local evidence, event order, question IDs, **toàn bộ concept lists**, timestamps, prefix length và mọi event không được chọn phải bất biến. Hai phía dùng cùng vị trí thay đổi. Lưu `changed_event_ids`, toàn bộ skill của chúng, `relation_mode`, quan hệ hierarchy audit và seed chọn vị trí.

### 6.2. Chỉ số và diễn giải

$$
\Delta_{\mathrm{LGT}}^{(i)}=\hat p_M(H_i^+,q_i)-\hat p_M(H_i^-,q_i).
$$

Hiệu ứng dương lớn cho thấy model nhạy với learner-global trend trong phần history không liên hệ theo luật đã khóa. Năng lực tổng quát vẫn có thể là lời giải thích hợp lệ, nhất là khi target concept mới/thưa; do đó đây chỉ là candidate shortcut khi effect quá mạnh so với local evidence, tạo overconfidence hoặc đi ngược dấu local evidence và lặp lại qua seed/dataset.

## 7. Quy trình và cổng quyết định

### P0 — Dataset audit và tái lập

- Khóa checksum raw data, pyKT commit/version, mapping ID, fold, seed, maxlen.
- Tạo data card cho Eedi và Algebra2005: question support, 0/1 support, multi-skill rate, raw-to-pyKT mapping, LGT relation coverage và số target khả thi.
- Xác minh item prior được tính từ đúng event train của fold, không gồm validation hay test; lưu danh sách item treatment trước khi đọc nhãn test.

### P1 — Baseline tự nhiên và source controls

- Huấn luyện DKT/SAINT/AKT trên train tự nhiên, đánh giá `test_natural`.
- Tạo `item_only`, `local_only`, `global_only` trên target tự nhiên như manipulation/source-profile checks.
- Dừng một case-dataset nếu support, label balance, target coverage hoặc LGT relation coverage không đạt ngưỡng đã khóa.

### P2 — IAP

- Sinh arm `prior_high`/`prior_low` theo từng item treatment, không sửa test.
- Huấn luyện lại, kiểm fingerprint test, thu $\Delta_{\mathrm{IAP}}$ và audit prior đạt được/số label đã sửa.

### P3 — LGT

- Sinh cặp `H0/H+/H-` trên cùng checkpoint tự nhiên từ P1.
- Kiểm toàn bộ invariant multi-skill/hierarchy trước forward; thu $\Delta_{\mathrm{LGT}}$.

### P4 — Review

- Báo cáo riêng Eedi (`hierarchy_aware`) và Algebra2005 (`exact_unrelated`).
- So sánh hướng/độ lớn qua DKT, SAINT, AKT, item, seed và dataset; xem các giải thích cạnh tranh trước khi quyết định `dừng`, `giữ ghi chú`, hay chuyển CĐ2.

| Cổng | Điều kiện vượt |
|---|---|
| G0 | Raw event, multi-skill map, train-fold và test fingerprint được kiểm chứng |
| G1 | Item/response support, target coverage và source controls đủ dùng |
| G2 | IAP chỉ đổi nhãn train chỉ định; LGT chỉ đổi event đủ điều kiện, local/target bất biến |
| G3 | Effect có hướng, ổn định qua seed và có diễn giải cạnh tranh rõ |
| G4 | Có lặp lại ở dataset thứ hai cùng giới hạn phát biểu minh bạch |

## 8. Artifact bắt buộc

```text
outputs/
  data_audits/<dataset>/
  train_interventions/<dataset>/<item>/<arm>/manifest.json
  checkpoints/<dataset>/<model>/<item-or-natural>/<arm>/seed_<seed>/
  predictions_natural/<dataset>/<model>/seed_<seed>.csv
  predictions_iap/<dataset>/<model>/<item>/seed_<seed>.csv
  predictions_lgt/<dataset>/<model>/seed_<seed>.csv
  summaries/<dataset>/<model>/IAP-01_*.csv
  summaries/<dataset>/<model>/LGT-01_*.csv
```

IAP artifact phải có prior gốc/đích/đạt được, ID label train thay đổi và fingerprint test. LGT artifact phải có ID event thay đổi, all-skill audit, relation mode và lý do loại event. Không đưa raw data hoặc artifact lớn vào Git.

## 9. Trạng thái triển khai

Mã nguồn hiện dùng IAP train label-edit và LGT all-skill relation gate. Chỉ chạy
screen sau khi smoke xác nhận raw-event mapping, metadata Eedi và GPU hoạt động.

## 10. Tài liệu liên quan

- [README.md](README.md): tóm tắt và trạng thái chạy.
- [case_cards/IAP-01.md](case_cards/IAP-01.md): card can thiệp train.
- [case_cards/LGT-01.md](case_cards/LGT-01.md): card can thiệp inference.
- [docs/dataset_panel.md](docs/dataset_panel.md): quyết định Eedi + Algebra2005.
- [docs/probe_protocol.md](docs/probe_protocol.md): invariant và audit.
- [IMPLEMENTATION.md](IMPLEMENTATION.md): hạng mục triển khai v0.2.
