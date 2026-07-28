# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `4/5` | Người dùng cần tìm phòng theo nhiều điều kiện như khu vực, ngân sách, tiện ích, sau đó so sánh lựa chọn và quyết định có đặt lịch xem hay không. |
| 🛠️ **Tool Interaction** | `5/5` | Bài toán cần tra cứu danh sách nhà trọ/căn hộ, kiểm tra lịch xem phòng còn trống và có thể thực hiện thao tác đặt lịch. Chatbot thường không tự xác nhận được các dữ liệu này. |
| 🔀 **Dynamic Decision** | `4/5` | Kết quả tìm phòng quyết định bước tiếp theo: nếu có phòng phù hợp thì kiểm tra lịch, nếu có slot thì đặt lịch, nếu không có thì gợi ý đổi tiêu chí. |
| ⏳ **Long Horizon** | `4/5` | Quy trình có nhiều bước liên tiếp từ lọc nhu cầu, tìm listing, kiểm tra slot, xác nhận đặt lịch và xử lý trường hợp lỗi hoặc hết lịch. |
| **TỔNG ĐIỂM FIT** | **17/20** | **KẾT LUẬN: BÀI TOÁN RẤT PHÙ HỢP ĐỂ DÙNG REACT AGENT VÌ CẦN TRA CỨU DỮ LIỆU VÀ THỰC HIỆN HÀNH ĐỘNG.** |

---

## 🧠 2. FAILURE MODES DỰ KIẾN CHO TOOL (ROLE 3)

| Tool dự kiến | Trường hợp có thể lỗi | Ví dụ input lỗi | Cách Agent nên phản ứng |
| :--- | :--- | :--- | :--- |
| `search_rentals` | Không tìm thấy phòng phù hợp với khu vực, ngân sách hoặc tiện ích người dùng yêu cầu. | `district="Quận 7", max_price=2 triệu, amenity="hồ bơi"` | Không bịa listing. Thông báo không có kết quả và đề xuất tăng ngân sách, đổi khu vực hoặc bỏ bớt tiện ích. |
| `search_rentals` | Người dùng nhập ngân sách không hợp lệ hoặc quá mơ hồ. | `"rẻ nhất có thể"`, `-1 triệu`, `"bao nhiêu cũng được"` | Hỏi lại ngân sách cụ thể hoặc dùng fallback lịch sự, không tự đoán giá. |
| `check_viewing_slots` | Mã phòng/căn hộ không tồn tại trong dữ liệu. | `listing_id="ABC-999"` | Báo rằng mã phòng không hợp lệ, yêu cầu người dùng chọn mã phòng từ danh sách đã tìm được. |
| `check_viewing_slots` | Không còn lịch xem phòng vào ngày/khung giờ mong muốn. | `preferred_day="Thứ Hai 23:00"` | Không xác nhận lịch. Gợi ý các khung giờ khác nếu tool trả về dữ liệu thay thế, hoặc yêu cầu chọn ngày khác. |
| `book_viewing` | Slot đặt lịch không hợp lệ hoặc không còn trống. | `slot="32/13 25:61"` | Từ chối đặt lịch, giải thích thời gian không hợp lệ và yêu cầu người dùng cung cấp khung giờ đúng. |
| `book_viewing` | Thiếu thông tin cần thiết để đặt lịch. | Thiếu tên người xem, số điện thoại, mã phòng hoặc slot cụ thể. | Hỏi lại thông tin còn thiếu trước khi gọi tool đặt lịch. |
| Toàn bộ tool | Agent gọi sai tên tool hoặc truyền sai số lượng tham số. | `find_house[]`, `book_viewing["Q7-101"]` | Parser/app trả lỗi có hướng dẫn cú pháp đúng; Agent tự sửa trong giới hạn `MAX_ITERATIONS`. |
| Toàn bộ tool | Agent lặp lại cùng một tool với cùng tham số dù đã nhận lỗi. | Gọi `check_viewing_slots["ABC-999"]` nhiều lần. | Kích hoạt guardrail, dừng vòng lặp và trả lời fallback lịch sự. |

**Kết luận Role 3:** Các tool trong bài toán thuê nhà có rủi ro chính là dữ liệu không tồn tại, tham số mơ hồ/sai định dạng, slot không còn trống và agent lặp lại hành động lỗi. Vì vậy System Prompt ở Mốc 3 cần nhấn mạnh: không tự bịa listing/lịch đặt, phải dựa trên Observation, và phải dừng an toàn khi quá `MAX_ITERATIONS`.

---

## 🔍 3. MỐC 2 - CHATBOT BASELINE EVALUATION (ROLE 5)

**Baseline protocol:** `system prompt + user message -> 1 LLM call -> final response`, số lần gọi tool = `0`.

### Prompt baseline đã dùng (Role 3)

Chatbot được yêu cầu tư vấn thuê nhà trọ/căn hộ bằng kiến thức có sẵn, nhưng không được gọi tool, không được tra cứu listing, không được xác nhận phòng còn trống, không được tự đặt lịch và không được bịa mã phòng/giá thuê/địa chỉ cụ thể.

### Kết quả thực tế sau khi chạy baseline

Role 4 đã chạy `run_baseline_chatbot()` thật trên cả 5 test case. Kết quả thực tế khớp gần như hoàn toàn với bảng dự đoán của Role 5.

| Test case | Kết quả thực tế | Khớp dự đoán? |
| :---: | :--- | :--- |
| #1 | Trả lời đầy đủ, đúng lý thuyết về điều khoản hợp đồng cọc. | `correct` |
| #2 | Trả lời đầy đủ, đúng lý thuyết về tránh lừa đảo cọc. | `correct` |
| #3 | Từ chối xác nhận phòng trống, không bịa mã phòng/địa chỉ cụ thể. | `safe fallback` |
| #4 | Từ chối tìm phòng và đặt lịch, yêu cầu nhân viên hoặc hệ thống có tool xác nhận. | `safe fallback` |
| #5 | Từ chối đặt lịch cho mã phòng/khu vực/ngày vô lý, không bịa kết quả đặt lịch. | `safe fallback` |

**Điểm đáng chú ý ở Test #3:** Dù không bịa mã phòng cụ thể, Chatbot vẫn tự đưa ra khoảng giá ước lượng như `3,5-4,5 triệu` / `4,5-5 triệu` dựa trên kiến thức chung thị trường. Đây là ranh giới mờ giữa `safe fallback` và hallucination nhẹ về số liệu thị trường, vì không có grounding từ tool hoặc database thật.

**Nhận xét Role 5:** Chatbot baseline phù hợp với các câu hỏi tư vấn lý thuyết (#1, #2), nhưng không giải quyết được các yêu cầu cần dữ liệu thực tế hoặc thao tác đặt lịch (#3, #4, #5). Test #3 là bằng chứng tốt cho luận điểm: chatbot nghe có vẻ hợp lý nhưng không có grounding thật, nên ReAct Agent có tool là cần thiết với đề tài thuê nhà.
