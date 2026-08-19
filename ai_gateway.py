import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def solve_problem(problem_text: str, user_language: str = "ar"):
    if not GEMINI_API_KEY:
        return {"error": "مفتاح Gemini مش موجود، ضيفو في ملف .env"}

    prompt = f"""
    أنت HumanOS، مساعد شخصي ذكي.
    المستخدم قال: "{problem_text}"

    قم بتحليل المشكلة وقدّم الحل في هذا الشكل (JSON فقط، من غير أي كلام زيادة):
    {{
        "diagnosis": "تشخيص المشكلة",
        "gaps": "الفجوات أو الأسباب",
        "solutions": ["حل أول", "حل ثاني"],
        "action_plan": "خطة تنفيذية للأسبوع القادم"
    }}
    اللغة: {user_language}
    """

    # ===== هادي هي التغييرة ====
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    # ===========================

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            return {
                "error": f"خطأ من Gemini (HTTP {response.status_code}): {response.text}"
            }
        
        data = response.json()
        
        if "candidates" not in data:
            return {
                "error": f"الرد من Gemini مش متوقع: {json.dumps(data, indent=2)[:800]}"
            }
        
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
        
        try:
            if text_response.startswith("```json"):
                text_response = text_response[7:-3]
            elif text_response.startswith("```"):
                text_response = text_response[3:-3]
            
            result_json = json.loads(text_response)
            return result_json
        except json.JSONDecodeError:
            return {"result": text_response}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"خطأ في الاتصال بـ Gemini: {str(e)}"}
    except Exception as e:
        return {"error": f"خطأ غير متوقع: {str(e)}"}