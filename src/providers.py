"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        # "gemini-2.5-flash" đã bị Google ngừng cấp cho tài khoản/API key mới (lỗi 404
        # NOT_FOUND). Dùng alias "gemini-flash-latest" để luôn trỏ tới bản Flash GA
        # mới nhất, tránh phải sửa code mỗi khi model cụ thể bị khai tử.
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-flash-latest"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """
    Offline Mock Provider (Cho bài test không cần kết nối API/không có API key).
    Mô phỏng đúng 3 loại system prompt của đề tài thuê nhà trọ: Planning, ReAct Agent,
    Chatbot Baseline — để `python src/app.py` vẫn chạy demo được ngay cả khi .env
    chưa cấu hình API key nào (đúng tinh thần "deterministic, chưa cần API key phức
    tạp ngay từ đầu" của bài lab).
    """
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        sp_lower = system_prompt.lower()
        text_lower = prompt.lower()

        # 1) Planning call (Bonus Cấp độ 4): chỉ liệt kê kế hoạch, không hành động
        if "lập kế hoạch" in sp_lower:
            if any(kw in text_lower for kw in ("tìm phòng", "tìm giúp", "đặt lịch", "chi phí")):
                return (
                    "Bước 1: Tra cứu phòng phù hợp bằng tool search_rentals.\n"
                    "Bước 2: Nếu người dùng cần đặt lịch/tính chi phí, gọi tiếp tool tương ứng."
                )
            return "Bước 1: Trả lời trực tiếp bằng kiến thức có sẵn, không cần gọi tool."

        # 2) Chatbot Baseline: không có tool trong system prompt -> không được gợi ý gọi tool
        if "search_rentals" not in sp_lower:
            return (
                "🤖 [Mock Provider]: Đây là câu trả lời demo ngoại tuyến, không có dữ liệu "
                "thời gian thực. Vui lòng cấu hình LLM_PROVIDER thật (gemini/openai/anthropic) "
                "trong file .env để nhận câu trả lời đầy đủ."
            )

        # 3) ReAct Agent: mô phỏng 1 bước gọi tool rồi tổng hợp Final Answer
        if "observation:" not in text_lower:
            if "cầu giấy" in text_lower:
                return 'Thought: Cần tra cứu phòng trọ ở Cầu Giấy.\nAction: search_rentals["Cầu Giấy", 5000000, ""]'
            if "quận 1" in text_lower or "quan 1" in text_lower:
                return 'Thought: Cần tra cứu phòng trọ ở Quận 1.\nAction: search_rentals["Quận 1", 7000000, ""]'
            return (
                "Thought: Đây là câu hỏi lý thuyết, không cần tra cứu dữ liệu thực tế.\n"
                "Final Answer: [Mock Provider] Đây là câu trả lời demo ngoại tuyến, không thay thế LLM thật."
            )

        return (
            "Thought: Đã có Observation ở bước trước, đủ dữ liệu để trả lời.\n"
            "Final Answer: [Mock Provider] Đây là câu trả lời demo ngoại tuyến dựa trên Observation phía trên."
        )


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
