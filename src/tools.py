"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo các công cụ tra cứu & đặt lịch xem phòng trọ / căn hộ.
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
        str: Danh sách các phòng trọ thỏa mãn điều kiện hoặc thông báo không tìm thấy.
    """
    try:
        district_clean = district.strip().lower()
        matched = []
        
        for item in MOCK_RENTALS_DB:
            # Kiểm tra quận
            if district_clean not in item["district"].lower():
                continue
            # Kiểm tra giá
            if max_price > 0 and item["price"] > max_price:
                continue
            # Kiểm tra loại phòng
            if room_type and room_type.lower() not in item["type"].lower():
                continue
                
            matched.append(item)
            
        if not matched:
            return f"Thông báo: Không tìm thấy phòng trọ nào ở '{district}' phù hợp với yêu cầu giá tối đa {max_price:,} VNĐ."
            
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
        room_id_clean = room_id.strip().upper()
        target_room = next((r for r in MOCK_RENTALS_DB if r["id"] == room_id_clean), None)
        
        if not target_room:
            return f"LỖI: Mã phòng '{room_id}' không tồn tại trong hệ thống. Vui lòng kiểm tra lại mã phòng."
            
        if target_room["status"] == "Đã cho thuê":
            return f"THÔNG BÁO: Phòng '{room_id}' ({target_room['title']}) đã được cho thuê. Rất tiếc không thể đặt lịch xem."
            
        return (
            f"✅ ĐẶT LỊCH XEM PHÒNG THÀNH CÔNG!\n"
            f"- Mã phòng: {target_room['id']} ({target_room['title']})\n"
            f"- Địa chỉ: {target_room['address']}\n"
            f"- Khách hàng: {customer_name} (SĐT: {phone})\n"
            f"- Thời gian hẹn: {viewing_time}\n"
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
        str: Bảng tính tổng chi phí dự kiến hàng tháng.
    """
    try:
        room_id_clean = room_id.strip().upper()
        target_room = next((r for r in MOCK_RENTALS_DB if r["id"] == room_id_clean), None)
        
        if not target_room:
            return f"LỖI: Không tìm thấy mã phòng '{room_id}' để tính chi phí."
            
        elec_cost = electricity_kwh * target_room["elec_rate"]
        water_cost = water_m3 * target_room["water_rate"]
        total = target_room["price"] + elec_cost + water_cost
        
        return (
            f"📊 BẢNG TÍNH CHI PHÍ DỰ KIẾN CHO PHÒNG {room_id_clean}:\n"
            f"- Giá thuê nhà: {target_room['price']:,} VNĐ\n"
            f"- Tiền điện ({electricity_kwh} kWh x {target_room['elec_rate']:,}đ): {elec_cost:,.0f} VNĐ\n"
            f"- Tiền nước ({water_m3} m3 x {target_room['water_rate']:,}đ): {water_cost:,.0f} VNĐ\n"
            f"👉 TỔNG CỘNG HÀNG THÁNG: {total:,.0f} VNĐ"
        )
    except Exception as e:
        return f"LỖI TÍNH CHI PHÍ: {str(e)}"


# Registered tools dictionary
AVAILABLE_TOOLS = {
    "search_rentals": search_rentals,
    "book_viewing": book_viewing,
    "calculate_monthly_cost": calculate_monthly_cost,
}
