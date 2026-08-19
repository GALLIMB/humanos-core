import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def solve_problem(problem_text: str, user_language: str = "ar"):
    if not GEMINI_API_KEY:
        return {"error": "مفتاح Gemini مش موجود، ضيفو في ملف .env"}

    prompt = f"""
    أنت HumanOS، مساعد شخصي ذكي.
    المستخدم قال: "{problem_text}"

    قم بتحليل المشكلة وقدّم الحل في هذا الشكل (JSON):
    {{
        "diagnosis": "تشخيص المشكلة",
        "gaps": "الفجوات أو الأسباب",
        "solutions": ["حل أول", "حل ثاني"],
        "action_plan": "خطة تنفيذية للأسبوع القادم"
    }}
    اللغة: {user_language}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"result": text_response}
    except Exception as e:
        return {"error": f"خطأ في الاتصال بـ Gemini: {str(e)}"}