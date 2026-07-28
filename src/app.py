"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS, PLANNING_PROMPT
from providers import get_llm_provider

load_dotenv()

# Chỉ những tool thuộc đúng đề tài thuê nhà mới được ReAct Agent gọi.
# get_weather/search_flights vẫn nằm trong AVAILABLE_TOOLS để tương thích ngược,
# nhưng REACT_SYSTEM_PROMPT cấm dùng -> nếu LLM lỡ gọi, Agent phải coi là ngoài phạm vi.
RENTAL_TOOL_NAMES = {"search_rentals", "book_viewing", "calculate_monthly_cost"}
REACT_TOOLS = {name: fn for name, fn in AVAILABLE_TOOLS.items() if name in RENTAL_TOOL_NAMES}

# Bắt "Action: ten_tool[tham_so]" (tham số có thể có dấu nháy hoặc không, có thể rỗng)
ACTION_PATTERN = re.compile(r"Action:\s*(\w+)\s*\[(.*?)\]")
# Bắt "Final Answer: ..." (lấy hết phần còn lại, kể cả xuống dòng)
FINAL_ANSWER_PATTERN = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)
# Tách tham số kiểu CSV có nháy: "Số 15, Ngõ 123", 5000000, "" -> giữ nguyên phần trong
# nháy kể cả khi chứa dấu phẩy, thay vì tách bừa theo mọi dấu phẩy.
ARG_SPLIT_PATTERN = re.compile(r'''\s*(?:"([^"]*)"|'([^']*)'|([^,]+))\s*(?:,|$)''')

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def parse_llm_output(text: str):
    """
    Tách phản hồi thô của LLM thành 1 trong 3 dạng:
      - ("final", answer, None)      -> LLM đã có Final Answer
      - ("action", tool_name, args)  -> LLM muốn gọi tool
      - ("invalid", None, None)      -> Không đúng định dạng bắt buộc
    """
    final_match = FINAL_ANSWER_PATTERN.search(text)
    if final_match:
        return "final", final_match.group(1).strip(), None

    action_match = ACTION_PATTERN.search(text)
    if action_match:
        tool_name = action_match.group(1).strip()
        raw_args = action_match.group(2).strip()
        return "action", tool_name, raw_args

    return "invalid", None, None


def parse_arguments(raw_args: str):
    """
    '"Cầu Giấy", 5000000, ""' -> ["Cầu Giấy", "5000000", ""].
    Nhận biết dấu nháy nên phần trong nháy chứa dấu phẩy (VD: địa chỉ "Số 15, Ngõ 123")
    không bị tách nhầm thành 2 tham số riêng.
    """
    if not raw_args.strip():
        return []
    args = []
    for m in ARG_SPLIT_PATTERN.finditer(raw_args):
        value = m.group(1) if m.group(1) is not None else (m.group(2) if m.group(2) is not None else m.group(3))
        args.append((value or "").strip())
    return args


def execute_tool(tool_name: str, raw_args: str) -> str:
    """
    Thực thi tool theo tên, chỉ trong phạm vi REACT_TOOLS (đúng đề tài thuê nhà).
    LUÔN trả về string (Observation) — lỗi tool là dữ liệu cho Agent suy luận,
    không phải lỗi làm crash chương trình.
    """
    if tool_name not in REACT_TOOLS:
        valid_tools = ", ".join(REACT_TOOLS.keys())
        return f"LỖI: Tool '{tool_name}' không tồn tại hoặc ngoài phạm vi đề tài. Các tool hợp lệ gồm: [{valid_tools}]"

    args = parse_arguments(raw_args)
    try:
        return REACT_TOOLS[tool_name](*args)
    except TypeError as e:
        return (
            f"LỖI: Tham số truyền cho tool '{tool_name}[{raw_args}]' không đúng số lượng/kiểu. "
            f"Chi tiết: {e}"
        )
    except Exception as e:
        return f"LỖI: Tool '{tool_name}' gặp sự cố khi thực thi: {e}"


def generate_plan(user_query: str, provider) -> str:
    """
    🎁 BONUS Cấp độ 4 - PLANNING: chia nhỏ mục tiêu người dùng thành các bước con
    TRƯỚC KHI Agent bắt đầu vòng lặp ReAct, thay vì chỉ phản ứng từng bước (Cấp 3).
    """
    response = provider.generate(user_query, system_prompt=PLANNING_PROMPT)
    return response.strip()


def summarize_memory(memory: list) -> str:
    """
    🎁 BONUS Cấp độ 4 - MEMORY: tóm tắt tối đa 3 lượt hỏi-đáp gần nhất thành ngữ
    cảnh hội thoại, cho phép người dùng hỏi tiếp kiểu "đặt lịch phòng vừa tìm được"
    mà không cần lặp lại toàn bộ chi tiết như Cấp 3 (mỗi câu hỏi độc lập, không nhớ gì).
    """
    if not memory:
        return ""

    lines = ["[BỘ NHỚ HỘI THOẠI - Các lượt hỏi đáp trước đó trong phiên này]"]
    for i, turn in enumerate(memory[-3:], 1):
        lines.append(f"Lượt {i} - Người dùng hỏi: {turn['question']}")
        lines.append(f"Lượt {i} - Agent đã trả lời: {turn['answer']}")
    lines.append("[HẾT BỘ NHỚ - Bên dưới là câu hỏi MỚI cần xử lý]\n")
    return "\n".join(lines) + "\n"


def run_react_agent(user_query: str, provider, memory_context: str = "", plan: str = "") -> dict:
    """
    Vòng lặp ReAct Agent thật: gọi LLM -> parse Action -> thực thi Tool ->
    chèn Observation thật vào prompt -> lặp lại cho tới Final Answer hoặc
    chạm phanh Guardrail MAX_ITERATIONS.

    memory_context và plan là 2 tham số BONUS Cấp độ 4 (tùy chọn, mặc định rỗng
    để không phá vỡ hành vi Cấp 3 gốc): nếu có, chúng được chèn vào đầu prompt
    làm ngữ cảnh bổ sung cho LLM trước khi suy luận Thought->Action.

    Trả về dict {"final_answer": str, "trace": [...], "guardrail_triggered": bool}
    để cả CLI (in ra console) lẫn giao diện web đều dùng chung 1 nguồn logic.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    plan_context = f"[KẾ HOẠCH ĐÃ LẬP]\n{plan}\n[HẾT KẾ HOẠCH]\n\n" if plan else ""

    transcript = ""        # Toàn bộ lịch sử Thought/Action/Observation đã tích lũy
    last_signature = None  # Để phát hiện Agent bị lặp lại đúng 1 hành động
    trace = []              # Lịch sử có cấu trúc để hiển thị lên giao diện web

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        prompt = f"{memory_context}{plan_context}Question: {user_query}\n{transcript}"
        response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        kind, payload, raw_args = parse_llm_output(response)

        if kind == "final":
            print(f"🧠 {response.strip()}")
            print(f"🏁 Final Answer: {payload}")
            trace.append({"step": step, "type": "final", "thought": response.strip(), "final_answer": payload})
            return {"final_answer": payload, "trace": trace, "guardrail_triggered": False, "plan": plan}

        if kind == "invalid":
            print(f"⚠️ LLM trả về sai định dạng:\n{response.strip()}")
            observation = (
                "LỖI: Không nhận diện được Action hoặc Final Answer. "
                "Định dạng bắt buộc: 'Action: ten_cong_cu[\"tham_so_1\", \"tham_so_2\"]'."
            )
            trace.append({"step": step, "type": "invalid", "thought": response.strip(), "observation": observation})
            transcript += f"{response.strip()}\nObservation: {observation}\n"
            continue

        tool_name, signature = payload, (payload, raw_args)
        print(f"🧠 {response.strip()}")

        if signature == last_signature:
            observation = (
                f"LỖI: Bạn vừa lặp lại chính xác '{tool_name}[{raw_args}]'. "
                "Hãy thử tham số khác hoặc đưa ra Final Answer nếu đã đủ dữ liệu."
            )
        else:
            observation = execute_tool(tool_name, raw_args)
        last_signature = signature

        print(f"👁️ Observation: {observation}")
        trace.append({
            "step": step, "type": "action", "thought": response.strip(),
            "tool": tool_name, "args": raw_args, "observation": observation,
        })
        transcript += f"{response.strip()}\nObservation: {observation}\n"

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
    fallback = (
        "Xin lỗi, tôi chưa thể hoàn tất yêu cầu này trong giới hạn bước xử lý cho phép. "
        "Bạn vui lòng thử lại với câu hỏi cụ thể hơn hoặc chia nhỏ yêu cầu."
    )
    print(f"🏁 Final Answer (Safe Fallback): {fallback}")
    trace.append({"step": MAX_ITERATIONS, "type": "guardrail", "final_answer": fallback})
    return {"final_answer": fallback, "trace": trace, "guardrail_triggered": True, "plan": plan}


def run_all_test_cases(provider):
    """Chạy toàn bộ test_cases.json trên cả Chatbot Baseline lẫn ReAct Agent để lấy trace log."""
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    for case in tests:
        print("\n" + "=" * 70)
        print(f"📌 TEST CASE #{case['id']} [{case.get('category', '')}]")
        print(f"   Kỳ vọng: {case.get('expected_behavior', '')}")
        print("=" * 70)

        run_baseline_chatbot(case["question"], provider)
        run_react_agent(case["question"], provider)


def run_one_test_case(provider, test_id: int = 1):
    """Chạy demo nhanh đúng 1 test case (mặc định #1) rồi thôi, để tiết kiệm quota LLM."""
    tests = load_test_cases()
    case = next((t for t in tests if t["id"] == test_id), tests[0])

    print(f"✅ Đã tải thành công {len(tests)} Test Cases — chỉ chạy demo Test #{case['id']}")
    print("\n" + "=" * 70)
    print(f"📌 TEST CASE #{case['id']} [{case.get('category', '')}]")
    print(f"   Kỳ vọng: {case.get('expected_behavior', '')}")
    print("=" * 70)

    run_baseline_chatbot(case["question"], provider)
    run_react_agent(case["question"], provider)


def run_interactive_mode(provider):
    """
    Chế độ chat trực tiếp: người dùng tự gõ câu hỏi và chọn Baseline hoặc ReAct Agent.

    🎁 BONUS Cấp độ 4: ReAct Agent ở đây có thêm Planning (tự lập kế hoạch trước khi
    hành động) và Memory (nhớ tối đa 3 lượt hỏi-đáp gần nhất trong cùng phiên chat).
    Chatbot Baseline KHÔNG có 2 tính năng này — giữ nguyên là "Cấp 2" để so sánh công bằng.
    """
    print("\n" + "=" * 70)
    print("💬 CHẾ ĐỘ TƯƠNG TÁC — Gõ câu hỏi của bạn (gõ 'exit' để thoát)")
    print("   🎁 ReAct Agent ở đây có Planning + Memory (Cấp độ 4)")
    print("=" * 70)

    session_memory = []  # Bộ nhớ hội thoại của ReAct Agent trong phiên hiện tại

    while True:
        user_query = input("\n👤 Bạn hỏi: ").strip()
        if not user_query:
            continue
        if user_query.lower() in ("exit", "quit", "thoat", "thoát"):
            print("👋 Tạm biệt!")
            break

        mode = input("   Chọn chế độ [1=Baseline Chatbot / 2=ReAct Agent / 3=Cả hai] (mặc định 2): ").strip()

        if mode == "1":
            run_baseline_chatbot(user_query, provider)
            continue

        # Từ đây trở đi luôn cần chạy ReAct Agent (mode 2 hoặc 3) -> áp dụng Planning + Memory
        if mode == "3":
            run_baseline_chatbot(user_query, provider)

        plan = generate_plan(user_query, provider)
        print(f"\n🗺️ Kế hoạch (Planning): {plan}")

        memory_context = summarize_memory(session_memory)
        result = run_react_agent(user_query, provider, memory_context=memory_context, plan=plan)

        session_memory.append({"question": user_query, "answer": result["final_answer"]})


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    run_one_test_case(provider, test_id=1)
    run_interactive_mode(provider)
