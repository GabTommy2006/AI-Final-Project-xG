# Giải thích pilot xG từng bước

## Bước 1 — Xác định một mẫu dữ liệu

Mỗi file events_<match_id>.json chứa nhiều loại sự kiện. Vòng for đọc từng event, chỉ giữ type.name == Shot. Một dòng shots.csv là một cú sút, không phải một trận hoặc một bàn thắng. match_id dùng truy vết và chia tập; event_id dùng kiểm tra trùng. ID không được đưa vào mô hình.

selected_matches.json chứa 100 trận đầu sau khi sắp theo ngày, rồi match_id. snapshot.json khóa phiên bản nguồn để lần sau lấy lại cùng dữ liệu. source_manifest.json lưu SHA-256 từng file, giống dấu kiểm tra nội dung file.

## Bước 2 — Tạo nhãn và giữ dữ liệu hợp lệ

shot.outcome.name == Goal tạo y=1; kết quả khác đã biết tạo y=0. Thiếu outcome thì y=None và loại khỏi tập mô hình, không tự gán thành không vào.

Ban đầu: 342.950 events, 2.647 Shot và 266 bàn. Có 19 penalty, trong đó 17 bàn. Sau loại penalty: 2.628 cú sút, 249 bàn. Chỉ giữ period 1–4, loại loạt luân lưu period 5. Non-penalty vẫn bao gồm đá phạt trực tiếp và sút sau phạt góc. Sự kiện phản lưới không phải Shot không được cộng vào nhãn của bảng này.

Bộ lọc nằm ở biến eligible. Không dùng toàn bộ shots.csv để train mà bỏ qua bộ lọc này.

## Bước 3 — Kiểm tra chất lượng dữ liệu (slide 6)

Counter đếm event_id, kiểm tra các ID xuất hiện nhiều lần. Kết quả pilot: không có ID trùng trong 342.950 events. Hai cú sút có cùng tọa độ không mặc nhiên là trùng.

Các cột x/y/outcome/body_part/type được kiểm tra không thiếu trên 2.647 cú sút. Đây là kết luận riêng cho pilot, không phải cả kho StatsBomb.

under_pressure vắng ở 2.119 cú sút và first_time vắng ở 1.930 cú sút. Code giữ cả giá trị raw và cờ present để phân biệt vắng field với False rõ ràng. Hai trường này chưa được dùng làm input baseline; không cần tự fillna(0) cả bảng.

## Bước 4 — Tạo khoảng cách và góc sút (slide 5)

Hệ tọa độ StatsBomb là 120 x 80. Tâm khung thành (120,40), hai cột (120,36) và (120,44). Đây là đơn vị tọa độ, không tự gọi là mét.

Với vị trí sút (x,y), dx=120-x:

    distance = sqrt(dx*dx + (y-40)*(y-40))
    angle = atan2(abs(8*dx), dx*dx + (y-40)*(y-40) - 16)

Góc là góc mở giữa hai hướng nhìn tới cột dọc, tính bằng radian. Dùng atan2 để xử lý đúng trường hợp góc lớn khi sút rất gần cầu môn. Code kiểm tra tọa độ hữu hạn trong miền. Pilot không có tọa độ không hợp lệ. Nếu mở rộng dữ liệu, bổ sung xử lý điểm suy biến ngay tại cột dọc trước khi áp dụng công thức.

Baseline chỉ dùng hai cột distance_sb_units và angle_rad. Body part, shot type và play pattern được trích xuất để khảo sát, chưa dùng train. provider_xg_reference_only chỉ giữ để tham chiếu, không thuộc X. Outcome chỉ tạo y. Không có end_location trong input.

## Bước 5 — Thống kê khoảng cách (slide 7)

Chia 2.628 shot hợp lệ thành nhóm và tính số bàn / số cú sút:

- 0 đến dưới 10: 402 sút, 93 bàn, 23,13%.
- 10 đến dưới 20: 963 sút, 119 bàn, 12,36%.
- 20 đến dưới 30: 988 sút, 32 bàn, 3,24%.
- Từ 30 trở lên: 275 sút, 5 bàn, 1,82%.

Đây là thống kê mô tả dữ liệu, KHÔNG phải xác suất mô hình gán cho mọi cú sút cùng nhóm. Không chứng minh nhân quả vì khoảng cách đi kèm những bối cảnh khác.

## Bước 6 — Chia train / validation / test (slide 8)

Sau sắp theo (match_date, match_id), lấy 60 trận đầu làm train, 20 tiếp theo validation, 20 cuối pilot test. Không chia ngẫu nhiên từng cú sút. Mọi cú sút trong một trận thuộc một tập, và code assert không giao match ID.

- Train: 60 trận, 1.586 sút, 131 bàn.
- Validation: 20 trận, 556 sút, 67 bàn.
- Test: 20 trận, 486 sút, 51 bàn.

Train học tham số. Pilot này cố định cấu hình, không tuning; validation và test chỉ báo kết quả sơ bộ. 60/20/20 là tỷ lệ TRẬN, nên số cú sút không nhất thiết chia đúng tỷ lệ đó.

## Bước 7 — Chuẩn hóa chỉ bằng train

Tính mean và std từ hai đặc trưng của train, rồi áp dụng cùng hai giá trị đó cho cả ba tập:

    standardized = (value - train_mean) / train_std

Không tính mean/std trên cả bộ trước chia tập. Cột toàn số 1 được thêm vào để học intercept. Vì vậy X có 3 cột: intercept, distance chuẩn hóa, angle chuẩn hóa.

## Bước 8 — Hai baseline và cách học

Baseline hằng: xác suất của mọi cú sút là tỷ lệ Goal của train, 131/1.586 = 8,26%. Không dùng tỷ lệ bàn test để tạo baseline.

Logistic Regression tính:

    z = intercept + beta_distance * distance_scaled + beta_angle * angle_scaled
    xG = sigmoid(z) = 1 / (1 + exp(-z))

Các beta được học từ train để giảm tổng negative log-likelihood nhị phân, cộng phạt L2:

    objective = sum(log(1+exp(z)) - y*z) + 0.5*(beta_distance**2 + beta_angle**2)

Intercept không phạt. Hệ số phạt L2=1 được chốt trước, không tuning. Đây là objective theo TỔNG loss, không mặc nhiên đồng nhất với C=1 trong một thư viện khác.

Code NumPy dùng Newton: tính gradient (hướng sai lệch) và Hessian (độ cong), giải hệ tuyến tính để cập nhật beta. Backtracking giảm bước nếu objective tăng. Dừng khi bước cập nhật rất nhỏ. Pilot hội tụ sau 6 vòng. Bạn chỉ cần giải thích logic tối ưu; không cần tuyên bố tự phát minh solver.

Hệ số trên dữ liệu đã chuẩn hóa xấp xỉ: intercept=-2,7353; distance=-0,8674; angle=0,0713. Với mô hình pilot này, khi giữ đặc trưng còn lại cố định, xa hơn làm giảm xác suất, góc rộng hơn làm tăng xác suất. Đây là quan hệ mô hình học, không phải kết luận nhân quả. Không dùng hệ số này trực tiếp cho khoảng cách/góc chưa chuẩn hóa.

## Bước 9 — Đọc metrics (slide 8)

Trên cùng 486 cú sút test:

- Constant: Log Loss 0,338855; Brier 0,094425; AUC 0,5000.
- Logistic: Log Loss 0,273940; Brier 0,080473; AUC 0,811449.

Log Loss = trung bình -[y*log(p)+(1-y)*log(1-p)]. Dự đoán sai nhưng quá tự tin bị phạt mạnh.

Brier = trung bình (p-y)^2. Cả Log Loss và Brier càng thấp càng tốt; không đổi các giá trị này thành phần trăm accuracy.

AUC đo khả năng xếp hạng: một shot ghi bàn được cho điểm cao hơn một shot không ghi bàn trong các cặp so sánh, hòa điểm tính một nửa. AUC 0,811 không phải dự đoán đúng 81,1% cú sút và không đảm bảo xác suất chuẩn.

Kết luận vừa đủ: Logistic hình học tốt hơn baseline hằng trên pilot này. Chưa chứng minh tốt hơn về thống kê, chưa chứng minh dùng tốt cho mọi giải. Hàm evaluate tự tính metrics; validate_results.py kiểm tra AUC độc lập bằng so sánh từng cặp và kiểm tra lại losses.

## Bước 10 — Calibration (slide 9)

Gộp dự đoán vào các bin rộng 0,1, rồi so mean(p) với tỷ lệ Goal. Bin là công cụ đánh giá, không phải bước huấn luyện. Không phải mọi cú sút trong bin có cùng xG.

- 0–<10%: 321 shot; dự báo trung bình 4,28%; thực tế 3,12%.
- 10–<20%: 124 shot; dự báo 14,94%; thực tế 18,55%.
- 20–<30%: 32 shot; dự báo 23,69%; thực tế 31,25%.
- 30–<40%: 7 shot; dự báo 33,01%; thực tế 85,71%.
- 40–<50%: 2 shot; dự báo 41,64%; thực tế 100%.

Bin cao chỉ có 7 và 2 shot, nên đường biểu đồ nhảy mạnh; không kết luận model gần như chắc chắn ghi bàn. Tổng hai bin trên 30% chỉ có 9 mẫu.

Trung bình toàn test: dự báo 8,84%, tỷ lệ Goal 10,49%. Đó là dấu hiệu dự báo thấp hơn thực tế trên tập này ở mức tổng thể; không đủ để mô tả calibration trên mọi nhóm. Pilot CHƯA chạy bước hiệu chỉnh sigmoid/isotonic. Nếu cần, fit hiệu chỉnh bằng validation hoặc CV trong train ở tuần 4, không fit trên final test.

## Bước 11 — Các file CSV có ý nghĩa gì?

shots.csv chứa cả 2.647 cú sút, có vị trí, nhãn và các thuộc tính audit. predictions.csv chỉ chứa 2.628 cú sút đủ điều kiện, có event_id, match_id, split, goal, constant_probability và logistic_xg. Nối hai file theo event_id để giải thích một dự đoán cụ thể. Outcome/goal dùng đối chiếu sau dự đoán, không nhập vào mô hình khi dự đoán cú sút mới.

Ví dụ học cách đọc: logistic_xg=0,20 nghĩa là ước lượng xác suất 20%, không đảm bảo 5 lần sẽ ghi đúng 1 bàn. Tổng xG mô tả kỳ vọng trên các cú sút đã quan sát, không chắc chắn bằng tỷ số và không phải dự báo đội thắng trước trận.

## Bước 12 — Tuần 2 khác tuần 3 thế nào?

Tuần 2: pilot nhỏ chứng minh tính khả thi, audit và baseline review. Tuần 3: Baseline Pipeline cho phạm vi mới, kiểm kê coverage, giữ split mới, lưu quy trình có thể chạy lại. Tuần 4: Model Improvement. Tuần 5: Integration & Reporting.

Pilot test đã được xem; không tiếp tục chọn cấu hình theo test này rồi gọi nó là unseen final test. Phạm vi mới gồm nhiều giải cần audit lại missing/schema, mức đại diện, và đánh giá theo giải khi đủ mẫu. Chỉ đổi tên scope không biến kết quả EPL pilot thành kết quả của phạm vi mới.

## Câu trả lời ngắn khi giáo viên hỏi

Hỏi: Em đã dùng input nào? — Hai đặc trưng: distance và angle. Body part/context mới trích xuất, chưa dùng baseline.

Hỏi: Đây có phải sklearn không? — Chưa; pilot là Logistic Regression được tối ưu bằng NumPy. sklearn là lựa chọn triển khai pipeline ở giai đoạn tiếp theo.

Hỏi: Sao không dùng accuracy? — Luôn đoán không vào đã đạt khoảng 90,53% trên dữ liệu eligible gộp nhưng không đánh giá được xác suất. Em dùng proper probability losses, AUC và calibration.

Hỏi: Vì sao giữ statsbomb_xg trong CSV? — Chỉ tham chiếu nguồn, không nằm trong X hoặc nhãn mô hình.

Hỏi: Em có tự làm chưa? — Chỉ nhận phần đã thực sự đọc/chạy/kiểm chứng. Nếu chưa: bộ mã được chuẩn bị với AI hỗ trợ; em đang chạy lại và tìm hiểu.

Hỏi: Con số nào thuộc phạm vi mới? — Chưa có kết quả nhiều giải. Các số trên slide pilot chỉ là 100 trận EPL 2015/16.

## Tài liệu đọc thêm

StatsBomb và điều khoản: https://github.com/hudl/open-data
Schema: https://github.com/hudl/open-data/tree/master/doc
Calibration: https://scikit-learn.org/stable/modules/calibration.html
Leakage: https://scikit-learn.org/stable/common_pitfalls.html
