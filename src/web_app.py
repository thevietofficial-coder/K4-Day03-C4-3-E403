"""
🌐 GIAO DIỆN WEB (Flask) — Lớp hiển thị cho Chatbot Baseline & ReAct Agent.
Tái sử dụng toàn bộ logic lõi trong app.py (không định nghĩa lại vòng lặp ReAct).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, render_template, request

from app import generate_plan, run_baseline_chatbot, run_react_agent, summarize_memory
from providers import get_llm_provider

app = Flask(__name__)
provider = get_llm_provider()

# 🎁 BONUS Cấp độ 4 - MEMORY: bộ nhớ hội thoại dùng chung cho phiên demo local
# (app này chỉ phục vụ 1 người dùng tại 1 thời điểm, nên dùng biến toàn cục là đủ).
session_memory = []


@app.route("/")
def index():
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    return render_template(
        "index.html",
        provider_name=provider.__class__.__name__,
        model_name=model_name,
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    mode = data.get("mode") or "agent"

    if not message:
        return jsonify({"error": "Vui lòng nhập câu hỏi."}), 400

    result = {}

    if mode in ("baseline", "both"):
        baseline_response = run_baseline_chatbot(message, provider)
        result["baseline"] = {"response": baseline_response}

    if mode in ("agent", "both"):
        plan = generate_plan(message, provider)
        memory_context = summarize_memory(session_memory)
        agent_result = run_react_agent(message, provider, memory_context=memory_context, plan=plan)
        result["agent"] = agent_result
        session_memory.append({"question": message, "answer": agent_result["final_answer"]})

    return jsonify(result)


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """🎁 Xoá bộ nhớ hội thoại để bắt đầu phiên chat mới."""
    session_memory.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print("==================================================")
    print("🏠 TRỢ LÝ TÌM NHÀ TRỌ — WEB UI")
    print("==================================================")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")
    print("🚀 Mở trình duyệt tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
