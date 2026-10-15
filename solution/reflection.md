# Reflection (≤1 page)

Fill this in before you submit.

**1. Which fault types were hardest to catch, and why? (Loại lỗi nào khó phát hiện nhất trong 5 luồng sự kiện?)**

- **Subtle Feature Skew and Drift (`feature_materialization` / `embedding_batch`)**:
  Các lỗi dạng `subtle` trong phân phối embedding (`centroid_shift`) và feature drift (`mean_shift_sigma`) có khoảng cách biến thiên nằm sát biên độ phương sai tự nhiên của dữ liệu sạch ($\approx 3\sigma$). Trong khi lỗi rõ rệt (`obvious`) có $\sigma > 1.8$, các lỗi tinh vi có $\sigma \in [0.97, 1.36]$ (so với nhiễu sạch tối đa là $\approx 0.472$). Nếu hạ ngưỡng quá thấp sẽ phát sinh False Positives và bị phạt rất nặng ($-30.0$ điểm cho FPR so với $+50.0$ cho TPR).
- **Subtle Lineage Runtime Anomalies (`lineage_run`)**:
  Một số đợt thực thi dbt job bị chậm ở mức tinh vi ($\approx 4400 - 4700$ ms), trong khi trần tối đa của các run bình thường có thể chạm mức $4805$ ms. Khi chỉ sử dụng một ngưỡng tĩnh duy nhất trên toàn hệ thống mà không có context lịch sử riêng cho từng dbt model, việc phân biệt giữa tắc nghẽn tài nguyên thoáng qua và lỗi hệ thống thực sự là vô cùng thách thức.

**2. How did you balance the cost/coverage tradeoff? (Quyết định cân bằng giữa chi phí gọi công cụ ctx.tools và TPR diễn ra như thế nào?)**

- **Quy tắc Single-Pass Metered Call**: Mỗi sự kiện chỉ được gọi đúng 1 công cụ đo lường chuyên biệt một lần duy nhất, tuyệt đối không gọi lặp để tránh cạn kiệt ngân sách.
- **Chấp nhận Overage nhỏ ở Public để tối đa hóa TPR**: Trong pha Public, ngân sách bị siết (220 credits cho 160 events), việc scan toàn diện tiêu tốn 240 credits (overage = 0.0909). Mức phạt overage chỉ là $-1.82$ điểm, trong khi giá trị mang lại từ việc bắt trúng lỗi giúp đạt TPR $= 0.9487$ ($+47.44$ điểm), mang lại điểm số tối ưu $45.62$ và duy trì mức **HIGH** cho toàn bộ 4 trụ cột.
- **Nguyên tắc Phòng thủ Zero-FPR**: Duy trì $\text{FPR} = 0.0\%$ là ưu tiên tối thượng vì báo động giả gây Alert Fatigue và làm sụt giảm nghiêm trọng tổng điểm vận hành.

**3. What statistical mechanism in ctx.state would you improve given more time? (Nếu có thêm thời gian, bạn sẽ cải tiến cơ chế thống kê nào trong ctx.state?)**

- **Thuật toán trực tuyến Welford (Online Welford's Algorithm)**: Lưu trữ bộ đếm $N$, trung bình động $\mu$, và phương sai động $M_2$ theo từng model / feature view riêng biệt trong `ctx.state`. Cơ chế này cho phép tự động hiệu chuẩn ngưỡng động $3\sigma$ thích ứng theo từng luồng dữ liệu thời gian thực thay vì phụ thuộc vào một ngưỡng tĩnh toàn cục.
- **Cửa sổ trượt (Sliding Window Moving Average)**: Ghi nhận thời gian thực thi của 10 lần chạy gần nhất cho mỗi dbt model trong `lineage_run` để phát hiện các runtime anomalies tinh vi dựa trên baseline cục bộ, vừa tăng TPR vừa triệt tiêu hoàn toàn nguy cơ False Positives.


