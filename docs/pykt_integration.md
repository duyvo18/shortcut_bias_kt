# Cách dự án tích hợp với pyKT

Thí điểm dùng gói `pykt-toolkit==0.0.38` trong môi trường do uv quản lý. Mã
pyKT không được chép vào dự án này.

## 1. pyKT phụ trách phần nào?

pyKT cung cấp:

- tiền xử lý dữ liệu thô thành `data.txt`;
- chia fold và tạo sequence chuẩn;
- lớp mô hình DKT, SAINT và AKT;
- vòng huấn luyện, đánh giá cơ bản và lưu trạng thái mô hình.

## 2. Dự án này phụ trách phần nào?

Dự án phụ trách:

- cấu hình YAML;
- bảng sự kiện chuẩn và định danh mục tiêu;
- hồ sơ tín hiệu tính từ train;
- cặp probe đối chứng;
- dự đoán tại mục tiêu được bảo vệ và báo cáo trường hợp.

## 3. Đường dẫn dữ liệu

YAML hiện trỏ tới bản Eedi đang có trong workspace để có thể tái hiện lần chạy
hiện tại. Khi dùng bản tải theo hướng dẫn pyKT, cần sửa `raw_path` và
`metadata_dir`. Không trộn file huấn luyện với thông tin mô tả từ hai bản tải khác nhau.

Bộ kết nối NIPS gọi trực tiếp bộ tiền xử lý cấp thấp của pyKT vì pyKT 0.0.38
mặc định tìm thông tin mô tả bên trong thư mục của file dữ liệu gốc, trong khi
cấu trúc Eedi thường đặt `train_data/` và `metadata/` cạnh nhau.

## 4. GPU và CPU

Máy chủ có RTX 3060 với 12 GiB VRAM và trình điều khiển báo tương thích CUDA
13.2. Mô hình và quá trình huấn luyện phải chạy trên CUDA. Tiền xử lý CSV và
bảng dữ liệu có thể dùng CPU; các vòng lặp Python tuần tự của pyKT không tự
động chạy song song chỉ vì tăng số luồng.
