# Reflection (≤1 page)

Fill this in before you submit.

**Which fault types were hardest to catch, and why?**

1. **Subtle Feature Skew and Drift (`feature_materialization` / `embedding_batch`)**:
   - Các lỗi dạng `subtle` trong phân phối embedding và feature drift có khoảng cách biến thiên nằm rất sát biên độ phương sai tự nhiên của dữ liệu sạch ($\approx 3\sigma$).
   - Ví dụ: Trong khi lỗi rõ rệt (`obvious`) có độ lệch $\sigma > 1.8$, các lỗi tinh vi (`subtle`) có $\sigma \in [0.97, 1.36]$, trong khi nhiễu ngẫu nhiên của dòng dữ liệu bình thường có thể lên đến $\sigma \approx 0.47$.
   - Nếu hạ ngưỡng quá thấp để bắt hết các lỗi này, hệ thống sẽ gặp hiện tượng báo động giả (**False Positives - FPR**). Do FPR có trọng số phạt rất nặng ($-30.0$ điểm trên công thức tính điểm so với $+50.0$ của TPR), việc đánh đổi quá mức nhạy cảm sẽ làm giảm mạnh tổng điểm vận hành.
2. **Subtle Lineage Runtime Anomalies (`lineage_run`)**:
   - Một số lần thực thi dbt job bị chậm ở mức tinh vi ($\approx 4400 - 4700$ ms), trong khi trần tối đa của các run bình thường có thể chạm mức $4805$ ms. Khi chỉ sử dụng một ngưỡng tĩnh duy nhất trên toàn hệ thống mà không có context lịch sử riêng cho từng dbt model, việc phân biệt giữa tắc nghẽn tài nguyên thoáng qua và lỗi hệ thống thực sự là vô cùng khó khăn.

**What would you change about your cost/coverage tradeoff, if you had another pass?**

1. **Cơ chế Phễu lọc Chi phí Thích ứng (Adaptive Cost Funnel)**:
   - Trong pha Public, ngân sách bị siết chặt (220 credits cho 160 sự kiện, tương đương $1.375$ credits/event), khiến việc quét $100\%$ các công cụ đo lường tốn kém (như `feature_drift` và `embedding_drift` tốn $2.0$ credits) gây ra vượt ngân sách nhẹ ($\approx 0.0909$ overage).
   - Nếu có thêm một vòng tối ưu, tôi sẽ sử dụng `ctx.state` để lưu lịch sử trượt (moving window statistics). Với các luồng dữ liệu có tính ổn định cao trong 5 chu kỳ liên tiếp, hệ thống có thể kiểm tra định kỳ (sampling rate: 50%) thay vì mọi chu kỳ, giúp tiết kiệm chi phí để ưu tiên ngân sách cho các pipeline quan trọng.
2. **Ưu tiên duy trì Zero-FPR làm nguyên tắc phòng thủ cốt lõi**:
   - Giữ FPR ở mức $0.0\%$ bảo vệ hệ thống khỏi án phạt điểm nặng nhất, đồng thời phản ánh đúng nguyên lý kỹ thuật dữ liệu thực tế: cảnh báo giả gây "Alert Fatigue", làm mất niềm tin của đội ngũ vận hành dữ liệu.

