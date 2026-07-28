"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo các công cụ tra cứu & đặt lịch xem phòng trọ / căn hộ.
Đảm bảo tất cả các hàm luôn trả về chuỗi thông báo (str), xử lý lỗi an toàn không crash app.
(Bao gồm cả get_weather và search_flights để tương thích ngược với code cũ trong app.py)
"""

# Cơ sở dữ liệu mẫu về phòng trọ
MOCK_RENTALS_DB = [
    {
        "id": "R101",
        "title": "Phòng trọ khép kín full đồ",
        "district": "Cầu Giấy",
        "price": 4500000,
        "type": "Phòng trọ",
        "address": "Số 15 Ngõ 123 Xuân Thủy, Cầu Giấy, Hà Nội",
        "status": "Còn trống",
        "elec_rate": 3500, # VNĐ/kWh
        "water_rate": 30000 # VNĐ/m3
    },
    {
        "id": "R102",
        "title": "Căn hộ dịch vụ 1PN sang trọng",
        "district": "Quận 1",
        "price": 6800000,
        "type": "Căn hộ dịch vụ",
        "address": "Số 88 Nguyễn Trãi, Quận 1, TP.HCM",
        "status": "Còn trống",
        "elec_rate": 4000,
        "water_rate": 100000 # VNĐ/người
    },
    {
        "id": "R103",
        "title": "Chung cư mini ban công thoáng mát",
        "district": "Cầu Giấy",
        "price": 3800000,
        "type": "Chung cư mini",
        "address": "Số 5 Ngách 20 Trần Thái Tông, Cầu Giấy, Hà Nội",
        "status": "Còn trống",
        "elec_rate": 3800,
        "water_rate": 25000
    },
    {
        "id": "R104",
        "title": "Phòng trọ sinh viên giá rẻ",
        "district": "Bình Thạnh",
        "price": 2800000,
        "type": "Phòng trọ",
        "address": "Số 42 Điện Biên Phủ, Bình Thạnh, TP.HCM",
        "status": "Đã cho thuê",
        "elec_rate": 3500,
        "water_rate": 20000
    }
]


def search_rentals(district: str, max_price: int = 0, room_type: str = "") -> str:
    """
    Tra cứu danh sách phòng trọ hoặc căn hộ cho thuê theo khu vực và ngân sách.
    
    Args:
        district (str): Quận/Huyện cần tìm (Ví dụ: 'Cầu Giấy', 'Quận 1', 'Bình Thạnh').
        max_price (int, optional): Mức giá thuê tối đa theo tháng (VNĐ). Mặc định 0 là không giới hạn.
        room_type (str, optional): Loại hình phòng ('Phòng trọ', 'Căn hộ dịch vụ', 'Chung cư mini').
        
    Returns:
        str: Danh sách các phòng trọ thỏa mãn điều kiện hoặc thông báo không tìm thấy / báo lỗi tham số.
    """
    try:
        if not district:
            return "LỖI THAM SỐ: Vui lòng cung cấp tên Quận/Khu vực cần tìm phòng."
            
        district_clean = str(district).strip().lower()
        
        try:
            max_price_num = float(max_price) if max_price else 0
        except (ValueError, TypeError):
            return f"LỖI THAM SỐ: Giá tối đa '{max_price}' không hợp lệ."

        room_type_clean = str(room_type).strip().lower() if room_type else ""

        matched = []
        for item in MOCK_RENTALS_DB:
            if district_clean not in item["district"].lower():
                continue
            if max_price_num > 0 and item["price"] > max_price_num:
                continue
            if room_type_clean and room_type_clean not in item["type"].lower():
                continue
            matched.append(item)

        if not matched:
            price_info = f" với giá tối đa {int(max_price_num):,} VNĐ" if max_price_num > 0 else ""
            return f"THÔNG BÁO: Không tìm thấy phòng trọ nào ở '{district}'{price_info}."

        results = [f"Tìm thấy {len(matched)} phòng phù hợp tại {district}:"]
        for r in matched:
            results.append(
                f"- [Mã phòng: {r['id']}] {r['title']} | Loại: {r['type']}\n"
                f"  Địa chỉ: {r['address']}\n"
                f"  Giá thuê: {r['price']:,} VNĐ/tháng | Trạng thái: {r['status']}"
            )
        return "\n".join(results)
    except Exception as e:
        return f"LỖI HỆ THỐNG TRA CỨU: {str(e)}"


def book_viewing(room_id: str, customer_name: str, phone: str, viewing_time: str) -> str:
    """
    Đặt lịch hẹn xem phòng trọ trực tiếp cho khách hàng.
    
    Args:
        room_id (str): Mã định danh của phòng (Ví dụ: 'R101', 'R102').
        customer_name (str): Họ và tên khách hàng hẹn xem phòng.
        phone (str): Số điện thoại liên hệ của khách hàng.
        viewing_time (str): Khung giờ và ngày xem phòng (Ví dụ: '15:00 ngày mai', '10:00 sáng thứ 7').
        
    Returns:
        str: Xác nhận đặt lịch thành công hoặc thông báo lỗi nếu mã phòng không tồn tại.
    """
    try:
        if not room_id:
            return "LỖI THAM SỐ: Vui lòng cung cấp mã phòng cần đặt lịch."
            
        room_id_clean = str(room_id).strip().upper()
        target_room = next((r for r in MOCK_RENTALS_DB if r["id"] == room_id_clean), None)
        
        if not target_room:
            return f"LỖI: Mã phòng '{room_id}' không tồn tại trong hệ thống. Vui lòng kiểm tra lại mã phòng."
            
        if target_room["status"] == "Đã cho thuê":
            return f"THÔNG BÁO: Phòng '{room_id}' ({target_room['title']}) đã được cho thuê. Rất tiếc không thể đặt lịch xem."
            
        cust_name = str(customer_name).strip() if customer_name else "Khách hàng"
        cust_phone = str(phone).strip() if phone else "Chưa cung cấp SĐT"
        v_time = str(viewing_time).strip() if viewing_time else "Chưa xác định thời gian"

        return (
            f"✅ ĐẶT LỊCH XEM PHÒNG THÀNH CÔNG!\n"
            f"- Mã phòng: {target_room['id']} ({target_room['title']})\n"
            f"- Địa chỉ: {target_room['address']}\n"
            f"- Khách hàng: {cust_name} (SĐT: {cust_phone})\n"
            f"- Thời gian hẹn: {v_time}\n"
            f"Chủ nhà/Quản lý phòng đã ghi nhận lịch hẹn và sẽ gọi xác nhận trước 30 phút."
        )
    except Exception as e:
        return f"LỖI ĐẶT LỊCH: {str(e)}"


def calculate_monthly_cost(room_id: str, electricity_kwh: float = 0, water_m3: float = 0) -> str:
    """
    Tính ước lượng tổng chi phí thuê phòng hàng tháng gồm giá nhà, tiền điện, tiền nước.
    
    Args:
        room_id (str): Mã phòng (Ví dụ: 'R101').
        electricity_kwh (float): Số ký điện dự kiến tiêu thụ trong tháng (kWh).
        water_m3 (float): Số khối nước dự kiến tiêu thụ trong tháng (m3).
        
    Returns:
        str: Bảng tính tổng chi phí dự kiến hàng tháng hoặc thông báo lỗi tham số.
    """
    try:
        if not room_id:
            return "LỖI THAM SỐ: Vui lòng cung cấp mã phòng để tính chi phí."

        room_id_clean = str(room_id).strip().upper()
        target_room = next((r for r in MOCK_RENTALS_DB if r["id"] == room_id_clean), None)
        
        if not target_room:
            return f"LỖI: Không tìm thấy mã phòng '{room_id}' để tính chi phí."

        try:
            kwh = float(electricity_kwh) if electricity_kwh else 0.0
            m3 = float(water_m3) if water_m3 else 0.0
        except (ValueError, TypeError):
            return f"LỖI THAM SỐ: Số điện ({electricity_kwh}) hoặc số nước ({water_m3}) phải là số."

        elec_cost = kwh * target_room["elec_rate"]
        water_cost = m3 * target_room["water_rate"]
        total = target_room["price"] + elec_cost + water_cost
        
        return (
            f"📊 BẢNG TÍNH CHI PHÍ DỰ KIẾN CHO PHÒNG {room_id_clean}:\n"
            f"- Giá thuê nhà: {target_room['price']:,} VNĐ\n"
            f"- Tiền điện ({kwh} kWh x {target_room['elec_rate']:,}đ): {elec_cost:,.0f} VNĐ\n"
            f"- Tiền nước ({m3} m3 x {target_room['water_rate']:,}đ): {water_cost:,.0f} VNĐ\n"
            f"👉 TỔNG CỘNG HÀNG THÁNG: {total:,.0f} VNĐ"
        )
    except Exception as e:
        return f"LỖI TÍNH CHI PHÍ: {str(e)}"


# --- COMPATIBILITY SHIMS (Để tương thích với code cũ trong app.py) ---
def get_weather(location: str) -> str:
    """Tra cứu thời tiết hiện tại của một thành phố (Hàm tương thích ngược)."""
    loc_lower = str(location).lower()
    if "hà nội" in loc_lower or "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%."
    elif "hồ chí minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return "Thời tiết TP.HCM: 33°C, Nắng nóng, Có mây."
    elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, Gió nhẹ, Mát mẻ."
    else:
        return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


def search_flights(origin: str, destination: str) -> str:
    """Tra cứu chuyến bay giữa hai địa điểm (Hàm tương thích ngược)."""
    return (
        f"Chuyến bay từ {origin} -> {destination} ngày mai:\n"
        f"1. VN123 (08:00) - Giá: 1,500,000 VNĐ (Còn vé)\n"
        f"2. VJ456 (14:30) - Giá: 1,200,000 VNĐ (Còn vé)"
    )


# Registered tools dictionary (Tổng hợp tất cả tool mới và cũ)
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "book_viewing": book_viewing,
    "calculate_monthly_cost": calculate_monthly_cost,
    "get_weather": get_weather,
    "search_flights": search_flights,
}
