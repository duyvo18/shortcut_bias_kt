# KẾ HOẠCH — Thí điểm kiểm tra sơ khảo các tín hiệu tắt trong truy vết tri thức

**Trạng thái:** kế hoạch thực nghiệm nội bộ v0.1 — trước triển khai  
**Cập nhật:** 28/08/2026  
**Phạm vi:** Chuyên đề 1 (CĐ1), phần kiểm định sơ khảo; không phải benchmark công bố, không phải thực nghiệm kết luận của luận án.

## 1. Bối cảnh và mục tiêu

Định hướng nghiên cứu xem *thiên lệch tín hiệu tắt* (shortcut bias) là tình
huống mô hình truy vết tri thức (Knowledge Tracing, KT) dựa quá mức vào một
quy luật thống kê dễ khai thác thay vì bằng chứng phù hợp để suy luận trạng
thái tri thức của người học theo từng khái niệm.

Thí điểm này kiểm tra **tính khả dĩ của giả định nghiên cứu**, không cố chứng
minh một kết luận cuối cùng về thiên lệch:

> Khi được huấn luyện bình thường trên dữ liệu KT tự nhiên, các mô hình nền có
> nhạy cảm đáng kể với một số tín hiệu tắt ứng viên hay không, trong khi bằng
> chứng tri thức trực tiếp được giữ cố định?

Hai tín hiệu tắt ứng viên ban đầu:

1. **Tỷ lệ đúng nền theo item (item-answer prior):** mô hình có để tỷ lệ nền
  của câu hỏi che mờ bằng chứng cục bộ theo khái niệm hay không?
2. **Xu hướng phản hồi chung của người học (learner-global trend/propensity):**
  mô hình có để các câu trả lời xa, ngoài khái niệm đích, kéo dự đoán quá mạnh
  hay không?

Thí điểm chỉ có thể đưa ra kết luận về **mức độ nhạy cảm với tín hiệu ứng viên**.
Không được dùng kết quả để kết luận:

- dữ liệu “có thiên lệch tín hiệu tắt”;
- câu hỏi dễ/khó là một tín hiệu không hợp lệ;
- người học thường trả lời đúng là một tín hiệu không hợp lệ;
- mô hình đã “mô hình hóa sai tri thức” chỉ từ một chênh lệch sàng lọc.

Lý do: độ khó câu hỏi và năng lực chung đều có thể là bằng chứng hợp lệ. Tín
hiệu tắt chỉ đáng lo khi tín hiệu ứng viên thay thế hoặc che mờ bằng chứng cần
thiết cho mục tiêu suy luận đã nêu.

## 2. Câu hỏi thí điểm và giới hạn phát biểu

### 2.1. Câu hỏi thí điểm

**PQ1 — Tỷ lệ đúng nền của câu hỏi.** Khi giữ cố định câu hỏi mục tiêu, dự đoán
của mô hình nền thay đổi thế nào nếu thay đổi có kiểm soát bằng chứng cục bộ
liên quan đến khái niệm đích? Độ nhạy đó có suy giảm có hệ thống ở các câu hỏi
có tỷ lệ nền cực cao hoặc cực thấp không?

**PQ2 — Xu hướng trả lời chung.** Khi giữ cố định câu hỏi, khái niệm đích và
bằng chứng cục bộ, dự đoán của mô hình nền thay đổi thế nào nếu hồ sơ trả lời ở
phần lịch sử xa/ngoài khái niệm đích chuyển từ chủ yếu đúng sang chủ yếu sai?

### 2.2. Chuỗi diễn giải bắt buộc

| Mức bằng chứng | Có thể nói gì | Không được nói gì |
|---|---|---|
| Hồ sơ nguồn | Tín hiệu có tồn tại, đủ độ phủ và có khả năng dự báo trong phân bố tập huấn luyện | Nguồn đó là tín hiệu tắt |
| Chênh lệch phép kiểm tra | Mô hình nhạy với tín hiệu ứng viên trong phép kiểm tra đã xác định | Mô hình chắc chắn đã dùng tín hiệu tắt trong dữ liệu thật |
| Mẫu hình có điều kiện | Có dấu hiệu dựa vào nguồn tín hiệu, có thể che mờ bằng chứng cục bộ trong điều kiện đã nêu | Sự thật nhân quả về năng lực hay quá trình học |
| Lặp lại và hiệu chuẩn | Trường hợp đủ mạnh để đưa vào danh mục nghiên cứu CĐ2 | Kết luận cho mọi dữ liệu và mô hình |

## 3. Nguyên tắc thiết kế

1. **Huấn luyện tự nhiên.** Tập huấn luyện và kiểm định giữ nguyên; không cài thiên lệch nhân tạo vào tập huấn luyện.
2. **Test gốc bất biến.** `test_natural` giữ nguyên để đo dự đoán và hiệu chuẩn thông thường.
3. **Phép kiểm tra là cặp đối chứng suy luận, không phải bộ đánh giá mới.** Mỗi cặp sinh từ một mục tiêu test gốc; câu hỏi, khái niệm, nhãn và thông tin mô tả của mục tiêu phải được khóa trước khi đổi phần lịch sử.
4. **Không dùng AUC trên dữ liệu đã sửa.** Câu trả lời trong phần lịch sử đã bị can thiệp không còn là nhãn quan sát hợp lệ cho đánh giá tuần tự. Chỉ đọc dự đoán tại mục tiêu đã khóa.
5. **Chỉ tính số liệu và ngưỡng từ tập huấn luyện.** Tỷ lệ nền, khoảng chia nhóm, ngưỡng support và quy tắc chọn trường hợp không được nhìn nhãn test trước.
6. **So sánh đối xứng.** Mỗi trường hợp có hai phiên bản `+`/`−`, không suy luận từ việc so một phép kiểm tra “cao” với toàn bộ test.
7. **Giữ các cách giải thích cạnh tranh.** Mỗi tài liệu đặc tả trường hợp phải nêu bằng chứng hợp lệ và các cách giải thích thay thế.

## 4. Panel dữ liệu và baseline v0

### 4.1. Dữ liệu

| Vai trò | Bộ dữ liệu pyKT | Lý do | Ghi chú |
|---|---|---|---|
| Chính | `nips_task34` | Eedi/NeurIPS 2020; có mã câu hỏi và khái niệm; mật độ tương tác theo câu hỏi thuận lợi cho trường hợp tỷ lệ nền | Ưu tiên chạy thử đầu tiên |
| Đối chứng | `assist2009` | Có mã câu hỏi và khái niệm; cấu trúc câu hỏi/khái niệm khác Eedi, dùng để kiểm tra mẫu hình có chỉ xuất hiện ở một bộ dữ liệu không | Kiểm tra tần suất câu hỏi trước khi chạy đầy đủ |

Không dùng `assist2015` cho trường hợp tỷ lệ nền của câu hỏi ở phiên bản đầu vì
cấu hình chuẩn pyKT không có mã câu hỏi ($num_q = 0$). Không đưa EdNet hay
Algebra2005 vào vòng đầu để giữ thí điểm nhỏ; đây là các lựa chọn mở nếu phiên
bản đầu có tín hiệu đáng chú ý.

### 4.2. Baseline

| Mô hình | Vai trò trong nhóm so sánh | Cách diễn giải |
|---|---|---|
| DKT | Mốc so sánh tuần tự theo khái niệm | Đối chứng: đường chạy chuẩn không đưa mã câu hỏi trực tiếp vào bước dự đoán |
| SAINT | Mô hình chú ý dùng câu hỏi và khái niệm | Kiểm tra nhóm mô hình chú ý có tiếp nhận thông tin câu hỏi không |
| AKT | Mô hình chú ý có câu hỏi, khái niệm và thành phần độ khó câu hỏi | Trường hợp nhạy nhất cho câu hỏi “tỷ lệ nền của câu hỏi có lấn át bằng chứng cục bộ không?” |
| DKVMN | Tùy chọn cho vòng hai | Bổ sung đại diện ghi nhớ nếu phiên bản đầu có tín hiệu |

Nhóm này là **nhóm mô hình học sâu dùng cho thí điểm**, không đại diện đầy đủ
cho mọi phương pháp KT. BKT/IRT/Rasch và các mô hình giảm thiên lệch chưa nằm
trong lần chạy đầu. Nếu CĐ1 được mở rộng thành benchmark có phát biểu mạnh hơn,
cần bổ sung các mô hình xác suất/đo lường và bộ so sánh phù hợp với mục tiêu.

### 4.3. Phạm vi chạy

| Giai đoạn | Bộ dữ liệu | Mô hình | Số lần lặp | Mục tiêu |
|---|---|---|---|---|
| Chạy thử | `nips_task34` | DKT, SAINT, AKT | 1 phần chia × 1 hạt giống | Kiểm tra toàn bộ quy trình, bộ thu dự đoán và tính khả thi của trường hợp |
| Sàng lọc | `nips_task34` | DKT, SAINT, AKT | 1 phần chia × 3 hạt giống | Ước lượng mẫu hình ban đầu và độ dao động giữa các hạt giống |
| Đối chứng chéo | `assist2009` | DKT, SAINT, AKT | 1 phần chia × 3 hạt giống | Kiểm tra mẫu hình có chỉ là đặc thù của Eedi không |

Không cần chạy chia 5 phần hoặc tối ưu tham số quy mô lớn ở thí điểm này. Mọi
mô hình dùng chung một quy trình tiền xử lý, cách chia dữ liệu, độ dài chuỗi và
ngân sách huấn luyện đã khóa trước. Nếu một trường hợp vượt cổng, khi đó mới
nâng quy mô lặp lại.

## 5. Dữ liệu, đặc trưng và hồ sơ tín hiệu

Mọi số liệu về tín hiệu được tính từ `train` (hoặc phần huấn luyện của fold) và
sau đó gắn vào mục tiêu test.

### 5.1. Tỷ lệ đúng nền theo câu hỏi

Với câu hỏi `q`:

$$
\hat\pi_q = \frac{\sum_{(u,t)\in \text{train}:Q_t=q} R_t}{\#\{(u,t)\in \text{train}:Q_t=q\}}.
$$

Chỉ giữ câu hỏi có số quan sát đủ lớn. Ngưỡng này phải được khóa trước khi xem
kết quả test; ưu tiên quy tắc dựa trên độ rộng khoảng tin cậy của $\hat\pi_q$,
thay vì giữ câu hỏi hiếm bằng một con số tùy tiện. Các nhóm `prior_high` và
`prior_low` dùng các phân vị cao/thấp của những câu hỏi đủ support.

### 5.2. Bằng chứng cục bộ theo khái niệm

Với mục tiêu `(u,t,q,c)`, tính từ các tương tác **trước** `t` của người học `u`:

- $n_{local}$: số tương tác trước đó thuộc khái niệm đích `c`;
- $r_{local}$: tỷ lệ trung bình có trọng số của các câu trả lời gần đây trên `c`;
- $recency_{local}$: khoảng cách từ lần gần nhất gặp `c` đến mục tiêu.

$E_{local}$ chỉ được xem là bằng chứng hợp lệ có khả năng sử dụng nếu có đủ
support và có quan hệ thực nghiệm với câu trả lời mục tiêu trên `test_natural`
sau khi điều kiện hóa hoặc ghép tương đồng phù hợp. Nếu không, việc mô hình
không phản ứng với $E_{local}$ không phải là bằng chứng về tín hiệu tắt.

### 5.3. Xu hướng trả lời chung của người học

Với cùng mục tiêu, tính hồ sơ trên lịch sử trước `t` **ngoài khái niệm đích**:

$$
G_{u,t,c}=\operatorname{mean}\{R_j: j<t, C_j\neq c\}.
$$

Ghi thêm số tương tác xa, độ dài chuỗi, thời gian/khoảng cách nếu bộ dữ liệu có
để kiểm tra mức chồng lấp. $G_{global}$ là tín hiệu ứng viên, không mặc nhiên
là nhiễu hay thiên lệch; nó có thể đại diện cho năng lực chung.

### 5.4. Kiểm soát chỉ dùng một nguồn tín hiệu

Trước phép kiểm tra trên mô hình, tạo hai bộ dự đoán đơn giản dùng số liệu tính
từ train:

- `item_only(q)` = $\hat\pi_q$;
- `learner_global_only(u,t,c)` = $G_{u,t,c}$.

Đánh giá chúng trên `test_natural` như **hồ sơ khả năng khai thác**, không như
mô hình KT cạnh tranh. Nếu nguồn tín hiệu không đủ support hoặc gần như không
có khả năng dự báo, dừng trường hợp tương ứng trước P3.

## 6. Định nghĩa “trường hợp” và cấu trúc phép kiểm tra

Một **trường hợp** không phải một dòng nhật ký riêng lẻ. Nó là một nhóm mục
tiêu kiểm tra đủ điều kiện, một tín hiệu ứng viên, bằng chứng cần giữ, cách
thay đổi phần lịch sử, cặp đối chứng và quy tắc diễn giải đã định trước.

Mẫu tài liệu đặc tả một trường hợp:

```text
Mã trường hợp:
Tín hiệu Z:
Nhóm mục tiêu và quy tắc đủ điều kiện:
Bằng chứng hợp lệ cần giữ V:
Cách giải thích thay thế và kiểm soát C:
Phần lịch sử gốc H0:
Hai phần lịch sử đối chứng H+ và H-:
Thông tin mục tiêu giữ cố định:
Chỉ số theo cặp và chỉ số tổng hợp:
Mẫu hình ủng hộ / không có tín hiệu / rủi ro:
```

### 6.1. Trường hợp IAP-01 — Tỷ lệ nền của câu hỏi có thể che mờ bằng chứng cục bộ

**Mục tiêu.** Kiểm tra độ nhạy với bằng chứng cục bộ có suy giảm ở mục tiêu có
$\hat\pi_q$ cực cao hoặc cực thấp hay không.

| Thành phần | Đặc tả v0 |
|---|---|
| `Z` | $\hat\pi_q$ tính từ tập huấn luyện |
| Mục tiêu | Mục tiêu test có câu hỏi `q` đủ support, khái niệm đích rõ và đủ `n_local` để tạo phép kiểm tra |
| Bằng chứng cần giữ `V` | Quan hệ người học–khái niệm thể hiện qua các câu trả lời gần đây trên khái niệm đích |
| Điều kiện hóa `C` | Cố định câu hỏi `q`; ghi/ghép theo độ dài phần lịch sử, khái niệm, support và hồ sơ ở khái niệm khác |
| $H_{local+}$ | Giữ câu hỏi/khái niệm/thời điểm trong lịch sử; đặt câu trả lời ở `k` tương tác gần nhất trên khái niệm đích theo hướng tốt |
| $H_{local-}$ | Như trên, nhưng câu trả lời ở cùng vị trí theo hướng kém |
| Mục tiêu khóa | Cùng `q`, cùng khái niệm, cùng nhãn thật; chỉ lấy dự đoán tại mục tiêu |

Với từng target `i`, tính:

$$
\Delta^{(i)}_{\rm local}
=\hat p_M(H^{(i)}_{\rm local+},q_i)
-\hat p_M(H^{(i)}_{\rm local-},q_i).
$$

So sánh phân bố $\Delta_{local}$ giữa `prior_high` và `prior_low`, đồng thời so
với mối liên hệ thật của $E_{local}$ và nhãn mục tiêu trong dữ liệu tự nhiên.
Mẫu hình đáng khảo sát là độ nhạy với bằng chứng cục bộ bị nén mạnh ở tỷ lệ nền
cực trị, kèm dự đoán bị neo gần $\hat\pi_q$.

**Không dùng:** so sánh AUC của toàn bộ test gốc với một nhóm test chỉ gồm câu
hỏi có tỷ lệ nền cao; khác biệt đó có thể hoàn toàn do độ khó câu hỏi hợp lệ.

### 6.2. Trường hợp LGT-01 — Xu hướng trả lời chung ở khái niệm mới hoặc thưa

**Mục tiêu.** Kiểm tra dự đoán có bị kéo mạnh bởi hồ sơ trả lời ở các khái niệm
khác khi khái niệm đích mới hoặc bằng chứng trực tiếp rất thưa hay không.

| Thành phần | Đặc tả v0 |
|---|---|
| `Z` | $G_{global}$, hồ sơ câu trả lời trong lịch sử ngoài khái niệm đích |
| Mục tiêu | Mục tiêu test thuộc khái niệm chưa xuất hiện hoặc có $n_{local}$ thấp trước mục tiêu |
| Bằng chứng cần giữ `V` | Câu hỏi `q`, khái niệm đích, đoạn lịch sử cục bộ và thông tin sẵn có |
| Giải thích cạnh tranh chính | Năng lực chung có thể là bằng chứng hợp lệ, nhất là ở khái niệm mới |
| $H_{global+}$ | Giữ sự kiện/câu hỏi/khái niệm/thời điểm; đổi câu trả lời ở đoạn xa sang hồ sơ chủ yếu đúng theo quy tắc đã khóa |
| $H_{global-}$ | Cùng vị trí xa, nhưng hồ sơ câu trả lời chủ yếu sai |
| Mục tiêu khóa | Cùng `q`, khái niệm, nhãn mục tiêu và bằng chứng cục bộ; chỉ lấy dự đoán tại mục tiêu |

Với từng target `i`:

$$
\Delta^{(i)}_{\rm global}
=\hat p_M(H^{(i)}_{\rm global+},q_i)
-\hat p_M(H^{(i)}_{\rm global-},q_i).
$$

$\Delta_{global}$ lớn cho thấy mô hình nhạy với hồ sơ trả lời ở các khái niệm
khác trong phép kiểm tra. Nó chỉ trở thành dấu hiệu cần nghiên cứu về sự dựa
vào tín hiệu khi mẫu hình không được giải thích thỏa đáng bởi bằng chứng hợp lệ
hoặc khi mức tác động không tương xứng với mối liên hệ của nhãn mục tiêu sau
khi điều kiện hóa/ghép tương đồng.

### 6.3. Quy tắc chung để tạo phép kiểm tra

1. Không đổi câu hỏi, khái niệm, nhãn mục tiêu, thứ tự sự kiện, độ dài chuỗi hay thời điểm nếu trường đó được mô hình sử dụng.
2. Chỉ thay đổi câu trả lời ở vị trí được ghi trong tài liệu đặc tả. Không dùng nhãn mục tiêu làm đầu vào.
3. Tạo cả `H+` và `H-`; `H0` là lịch sử tự nhiên để tham chiếu, không phải đối chứng duy nhất.
4. Ghi mã trường hợp, mã mục tiêu gốc, mã chuỗi, biến thể, vị trí thay đổi và hạt giống tạo phép kiểm tra.
5. Đây là đầu vào đối chứng được thiết kế có chủ đích; không gọi nó là lịch sử học tập thật và không tính AUC trên câu trả lời đã sửa.
6. Kiểm tra hồ sơ sau thay đổi: độ dài chuỗi, số mục tiêu, giá trị tín hiệu và độ phủ; loại phép kiểm tra không đạt điều kiện đã khóa.

## 7. Quy trình triển khai

### P0 — Khóa dữ liệu và bảo đảm tái lập

- Ghi phiên bản/commit pyKT, Python/PyTorch/CUDA, checksum dữ liệu gốc, cấu hình tiền xử lý, phần chia dữ liệu, độ dài chuỗi và hạt giống.
- Chạy tiền xử lý một lần; lưu phần chia dữ liệu và ánh xạ câu hỏi/khái niệm.
- Kiểm tra rò rỉ dữ liệu: người học/sự kiện không xuất hiện sai phần; số liệu $\hat\pi_q$ và $G_{global}$ chỉ tính từ train; không dùng nhãn test để đặt quy tắc.
- Lưu thẻ dữ liệu rút gọn: số người học, câu hỏi, khái niệm, tương tác, độ phủ câu hỏi–khái niệm, tần suất câu hỏi và tỷ lệ chuỗi có mục tiêu đủ điều kiện.

### P1 — Mô hình nền và bộ thu dự đoán

- Huấn luyện DKT, SAINT, AKT theo cấu hình đã khóa.
- Lưu dự đoán tại từng mục tiêu test cùng `event_id`, mã người học nội bộ, mã câu hỏi, mã khái niệm, nhãn mục tiêu, vị trí chuỗi và hạt giống.
- Báo cáo AUC/NLL/Brier/ECE trên `test_natural` chỉ để kiểm mô hình chạy bình thường; không xếp hạng mô hình theo chênh lệch AUC rất nhỏ.
- Viết bộ đánh giá riêng theo dạng `prefix -> một mục tiêu được bảo vệ`; không đưa `H+`/`H-` vào bộ đánh giá chuỗi chuẩn của pyKT.

### P2 — Hồ sơ khả năng khai thác và cổng khả thi

- Tính $\hat\pi_q$, $E_{local}$, $G_{global}$ từ train/lịch sử hợp lệ.
- Chạy `item_only` và `learner_global_only` trên `test_natural`.
- Kiểm tra support, mức chồng lấp và số cặp đủ điều kiện theo từng nhóm.
- Dừng trường hợp nếu nguồn tín hiệu quá thưa, không có phần chồng lấp, không đo được bằng chứng cục bộ hoặc thay đổi tạo ra đầu vào quá xa dữ liệu tự nhiên.

### P3 — Tạo phép kiểm tra và đo chênh lệch sàng lọc

- Tạo `IAP-01` và `LGT-01` cho đúng mục tiêu đủ điều kiện; không thay đổi `test_natural`.
- Chạy cùng trạng thái mô hình trên `H0`, `H+`, `H-`.
- Tính trung bình/trung vị, phân vị, khoảng bootstrap theo mục tiêu và độ dao động giữa các hạt giống.
- Lưu dự đoán của từng cặp để kiểm tra trường hợp lỗi, không chỉ lưu số liệu tổng hợp.

### P4 — Xem xét và quyết định

- So sánh hướng/độ lớn của chênh lệch giữa DKT, SAINT, AKT, các hạt giống và hai bộ dữ liệu.
- Đối chiếu với bằng chứng cục bộ, kết quả tự nhiên, cách giải thích thay thế và rủi ro về độ tin cậy.
- Viết hồ sơ ứng viên cho từng tổ hợp `nguồn tín hiệu × bộ dữ liệu × mô hình`.
- Quyết định: `dừng`, `giữ ghi chú về độ nhạy`, `đưa vào danh mục CĐ2`, hoặc `nâng thành trường hợp đại diện tiềm năng cho CĐ3`.

### P5 — Kiểm soát dương/âm (tùy chọn, sau P4)

Nếu P3 có tín hiệu nhưng độ tin cậy của chỉ số chưa rõ, tạo một phép kiểm tra
bán tổng hợp riêng: cài một mối liên hệ đã biết trước vào **train** và kiểm tra
xem phép kiểm tra/bộ đánh giá có phản ứng đúng chiều hay không. P5 kiểm tra
quy trình; nó không phải bằng chứng tín hiệu tắt tồn tại tự nhiên trong dữ liệu.

## 8. Chỉ số và quy tắc diễn giải

| Nhóm | Chỉ số | Vai trò |
|---|---|---|
| Kiểm tra hoạt động | AUC, NLL/BCE, Brier, ECE trên `test_natural` | Kiểm mô hình nền hoạt động và hiệu chuẩn cơ bản |
| Khả năng khai thác | điểm của `item_only`, `learner_global_only`; support/độ phủ | Nguồn tín hiệu có thể được mô hình khai thác không? |
| Phép kiểm tra item | $\Delta_{local}$ theo nhóm tỷ lệ nền | Mô hình còn phản ứng với bằng chứng cục bộ không? |
| Phép kiểm tra người học | $\Delta_{global}$ | Mô hình nhạy với hồ sơ ở khái niệm khác đến mức nào? |
| Độ ổn định | dao động giữa hạt giống, khoảng bootstrap theo mục tiêu, hướng qua bộ dữ liệu | Mẫu hình có đủ bền cho CĐ2 không? |
| Độ tin cậy | mức chồng lấp, độ cân bằng, kiểm tra hồ sơ quá khác dữ liệu, giải thích thay thế | Giới hạn phát biểu |

Không có ngưỡng độ lớn tác động “chuẩn” cho thí điểm. Một tín hiệu chỉ được
ưu tiên khi có: (i) support đủ; (ii) dấu giống nhau qua các hạt giống; (iii) ít
nhất một đối chứng chéo hoặc kiểm soát dương; và (iv) cách giải thích dựa trên
bằng chứng/đối chứng thay thế rõ ràng hơn một chênh lệch AUC đơn thuần.

## 9. Rủi ro về độ tin cậy và cách xử lý

| Rủi ro | Hệ quả | Kiểm soát |
|---|---|---|
| Độ khó câu hỏi là bằng chứng hợp lệ | Nhầm việc dùng thông tin câu hỏi thành thiên lệch | Giữ câu hỏi mục tiêu cố định; kiểm tra độ nhạy với bằng chứng cục bộ, không chỉ so sánh câu hỏi có tỷ lệ nền cao/thấp |
| Năng lực chung là bằng chứng hợp lệ | Nhầm xu hướng trả lời chung thành tín hiệu tắt | Giữ/điều kiện hóa bằng chứng theo khái niệm; ghi cách giải thích thay thế; tối đa chỉ phát biểu về độ nhạy/ứng viên |
| Phép kiểm tra quá xa dữ liệu thật | Chênh lệch do đầu vào phi thực tế | Không đổi chuỗi sự kiện/câu hỏi/khái niệm/thời gian; kiểm tra hồ sơ; dùng hai phía đối xứng |
| Rò rỉ số liệu | Tỷ lệ nền hoặc nguồn tín hiệu đã nhìn nhãn test | Tính toàn bộ số liệu/ngưỡng từ train |
| Tính AUC trên lịch sử đã sửa | Chỉ số không còn ý nghĩa | Chỉ đọc dự đoán tại mục tiêu được bảo vệ |
| Khác biệt thành phần tập con | Nhầm khác biệt tập con thành thiên lệch | Ghép/cân bằng/chia nhóm; không so test tổng với nhóm tỷ lệ nền cao |
| Dao động giữa hạt giống/mô hình | Mẫu hình chỉ do ngẫu nhiên | Chạy 3 hạt giống; báo cáo phân bố theo cặp và khoảng tin cậy |
| Chia nhóm theo kiến trúc | Lệch khỏi mục tiêu kiểm tra tín hiệu | Họ mô hình chỉ là nhóm so sánh; nguồn tín hiệu/bằng chứng/điều kiện mới là đơn vị trường hợp |

## 10. Sản phẩm và cấu trúc dự kiến

```text
research_direction/
  PLAN.md
  experiment_shortcut_pilot/
    configs/
      smoke.yaml
      screen.yaml
    data_cards/
      nips_task34.md
      assist2009.md
    case_cards/
      IAP-01.md
      LGT-01.md
    scripts/
      build_source_profile.py
      collect_target_predictions.py
      build_probes.py
      evaluate_probes.py
    outputs/
      source_profiles/
      predictions_natural/
      predictions_probe/
      candidate_dossiers/
      pilot_report.md
```

Các file trong `outputs/` chỉ được coi là hiện vật thí điểm sau khi P0–P4 chạy
xong. Không đưa dữ liệu thô hay tệp kết quả lớn vào thư mục tài liệu.

## 11. Cổng quyết định và tiêu chí dừng

| Cổng | Điều kiện vượt | Nếu không vượt |
|---|---|---|
| G0 — Tái lập | Mô hình nền huấn luyện/đánh giá được, ánh xạ mục tiêu đúng | Sửa quy trình trước khi làm phép kiểm tra |
| G1 — Khả năng khai thác | Nguồn tín hiệu có support, chồng lấp và bộ dự đoán đơn giản không vô nghĩa | Dừng nhóm tín hiệu ở bộ dữ liệu đó |
| G2 — Hợp lệ phép kiểm tra | `H+`/`H-` giữ đúng mục tiêu và không tạo hồ sơ quá phi lý | Sửa tài liệu đặc tả/cách tạo phép kiểm tra |
| G3 — Tín hiệu ứng viên | Chênh lệch có hướng rõ, ổn định qua hạt giống, có giải thích kiểm soát được | Giữ ghi chú về độ nhạy hoặc dừng |
| G4 — Danh mục CĐ2 | Có nguồn, bằng chứng cần giữ, đối chứng, giới hạn và cách giải thích rõ | Không nâng trường hợp lên CĐ2/CĐ3 |

## 12. Việc cần làm tiếp theo

1. Xác nhận phiên bản pyKT và tải/chạy được `nips_task34` theo tiền xử lý hiện hành.
2. Viết thẻ dữ liệu `nips_task34`, gồm độ phủ câu hỏi–khái niệm, tần suất câu hỏi và các trường có thể dùng.
3. Chạy thử DKT/SAINT/AKT, đồng thời kiểm tra bộ thu dự đoán có truy vết được sự kiện mục tiêu.
4. Khóa định nghĩa vận hành của $E_{local}$, $G_{global}$, ngưỡng support và quy tắc tạo `H+`/`H-` trước khi xem kết quả.
5. Viết hai tài liệu đặc tả IAP-01 và LGT-01; chỉ sau đó mới tạo phép kiểm tra.
6. Sau khi chạy thử, quyết định có đủ điều kiện để chạy sàng lọc 3 hạt giống và đối chứng chéo `assist2009` hay không.

## 13. Tài liệu liên quan

- [README.md](README.md): phạm vi và quy ước của bộ tài liệu về tín hiệu tắt.
- [01_dinh_huong_nghien_cuu.md](01_dinh_huong_nghien_cuu.md): định hướng và logic CĐ1–CĐ3.
- [03_phan_tich_chuyen_de.md](03_phan_tich_chuyen_de.md): quy trình/cổng CĐ1, hồ sơ ứng viên và tài liệu đặc tả trường hợp ở mức rộng hơn.
- [research_direction.pdf](research_direction.pdf): bản PDF đặc tả định hướng ban đầu.

## 14. Tài liệu kỹ thuật đã tham khảo

- [pyKT datasets](https://pykt-toolkit.readthedocs.io/en/latest/datasets.html)
- [pyKT models](https://pykt-toolkit.readthedocs.io/en/latest/models.html)
- [pyKT data configuration](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/configs/data_config.json)
- [pyKT training dispatcher](https://raw.githubusercontent.com/pykt-team/pykt-toolkit/main/pykt/models/train_model.py)

