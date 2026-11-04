# Week 2 xG Pilot — Hướng dẫn chạy

## 1. Phạm vi đúng của gói này

Đây là code tạo ra số liệu pilot trong slide tuần 2: 100 trận đầu theo (match_date, match_id) của Premier League 2015/16, ngày 08/08–25/10/2015. Snapshot nguồn đã cố định trong snapshot.json. Gói này CHƯA chạy phạm vi mới gồm nhiều giải châu Âu và World Cup. Không đổi bộ lọc rồi tiếp tục dùng số liệu cũ trên slide.

Nguồn: https://github.com/hudl/open-data

## 2. Chuẩn bị trên Windows

Dùng Python 3.11–3.14, có pip; môi trường hiện tại sử dụng Python 3.11. NumPy 2.3.5 không hỗ trợ Python 3.15. Giải nén ZIP vào thư mục dễ tìm, ví dụ Documents/week2-pilot. Mở thư mục bằng VS Code rồi chọn Terminal > New Terminal. Hoặc mở PowerShell tại đúng thư mục có audit_xg.py.

Tạo môi trường riêng và cài NumPy:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Không cần activate nên không cần thay đổi ExecutionPolicy. Nếu máy không có lệnh py nhưng có python, thay py bằng python ở lệnh tạo môi trường. Sau đó dùng đúng đường dẫn .venv như bên trên.

## 3. Cách A: kiểm tra ngay kết quả có sẵn, không cần tải JSON

```powershell
.\.venv\Scripts\python.exe validate_results.py
.\.venv\Scripts\python.exe show_results.py
```

Lệnh đầu kiểm tra số liệu, chia tập, hình học và lời giải mô hình từ CSV/JSON có sẵn. Kết quả mong đợi: checks = passed. Lệnh thứ hai in các con số trong slide. Cách A KHÔNG tải raw và KHÔNG huấn luyện lại từ đầu.

## 4. Cách B: chạy lại toàn bộ từ dữ liệu nguồn

```powershell
.\.venv\Scripts\python.exe download_data.py
.\.venv\Scripts\python.exe audit_xg.py
.\.venv\Scripts\python.exe validate_results.py
.\.venv\Scripts\python.exe show_results.py
```

Bước tải cần Internet, tải khoảng 295 MB JSON và có thể mất vài phút hoặc lâu hơn theo mạng. Không cần tải cả kho. Script tải đúng snapshot và kiểm tra SHA-256 của từng file events. Nếu mạng lỗi, chạy lại download_data.py; file đã tải đúng sẽ được tái sử dụng. Không chạy audit trước khi tải đủ 100 file.

Các bước audit, huấn luyện và kiểm chứng sau đó chạy offline. audit_xg.py ghi đè các kết quả CSV/JSON trong thư mục này; bản kết quả gốc có thể lấy lại từ ZIP. Không xóa snapshot.json hoặc source_manifest.json trước khi tải.

PowerShell 7 là lựa chọn khác: ./download.ps1 -Limit 100. Windows PowerShell 5 không hỗ trợ ForEach-Object -Parallel; ưu tiên download_data.py.

Trên macOS/Linux: tạo môi trường bằng python3 -m venv .venv, sau đó thay đường dẫn Python trong các lệnh trên bằng .venv/bin/python.

## 5. Đọc file nào trước?

1. STEP_BY_STEP_VI.md: giải thích dữ liệu, thuật toán và các kết quả.
2. audit_xg.py: trích xuất, audit, tạo đặc trưng, chia tập, huấn luyện và đánh giá.
3. show_results.py: đọc kết quả theo slide.
4. validate_results.py: kiểm tra độc lập các kết quả đã tính.
5. download_data.py: tải dữ liệu bằng thư viện chuẩn Python.

## 6. Các file đầu ra

- shots.csv: toàn bộ 2.647 Shot, gồm cả penalty; KHÔNG phải tất cả đều dùng train.
- predictions.csv: 2.628 shot non-penalty đủ điều kiện, có split và xác suất của hai baseline.
- audit.json: số lượng, missing, duplicates và giới hạn dữ liệu.
- group_summaries.json: thống kê mô tả theo nhóm, dùng cho biểu đồ khoảng cách.
- model_metrics.json: split, hệ số, cấu hình, metrics và calibration.
- split_matches.json: danh sách match ID theo tập.
- source_manifest.json: URL và SHA-256 nguồn.
- validation.json: kết quả kiểm chứng.

Đọc điều khoản nguồn trước khi sử dụng/công bố. Raw JSON không đóng gói trong ZIP.

