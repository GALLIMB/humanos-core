import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def solve_problem(problem_text: str, user_language: str = "ar"):
    if not GEMINI_API_KEY:
        return {"error": "❌ مفتاح Gemini غير موجود في ملف .env"}
    
    if not problem_text or len(problem_text.strip()) < 3:
        return {"error": "❌ المشكلة قصيرة جداً. اكتب وصفاً أوضح."}

    prompt = f"""
    أنت HumanOS، مستشار ذكي. المستخدم قال: "{problem_text}"

    حلل هذه المشكلة وقدّم إجابة عملية وواضحة بهذا الشكل (JSON فقط، بدون أي كلام إضافي):
    {{
        "diagnosis": "تشخيص دقيق للمشكلة",
        "gaps": "الفجوات أو الأسباب الرئيسية",
        "solutions": ["حل عملي 1", "حل عملي 2", "حل عملي 3"],
        "action_plan": "خطة تنفيذية خطوة بخطوة للأسبوع القادم"
    }}
    اللغة: {user_language}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            return {"error": f"❌ خطأ من Gemini (HTTP {response.status_code}): {response.text[:200]}"}
        
        data = response.json()
        
        if "candidates" not in data or not data["candidates"]:
            return {"error": "❌ لم يتلقَ النظام رداً صحيحاً من Gemini"}
        
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # تنظيف النص من علامات Markdown
        clean_text = text_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        try:
            result = json.loads(clean_text)
            # التأكد من وجود الحقول المطلوبة
            for key in ["diagnosis", "gaps", "solutions", "action_plan"]:
                if key not in result:
                    result[key] = "لا يوجد"
            return result
        except json.JSONDecodeError:
            # إذا لم يكن JSON صحيحاً، نعيد النص كـ نتيجة
            return {
                "diagnosis": text_response[:300],
                "gaps": "لم يتم تحليل الفجوات",
                "solutions": ["راجع النص أعلاه"],
                "action_plan": text_response[300:600] if len(text_response) > 300 else "يرجى مراجعة التحليل"
            }
            
    except requests.exceptions.Timeout:
        return {"error": "❌ انتهت مهلة الاتصال بـ Gemini. حاول مرة أخرى."}
    except requests.exceptions.RequestException as e:
        return {"error": f"❌ خطأ في الاتصال: {str(e)}"}
    except Exception as e:
        return {"error": f"❌ خطأ غير متوقع: {str(e)}"}

def simulate_future(age: int, job: str, income: float, skills: str, goal: str, language: str = "ar"):
    if not GEMINI_API_KEY:
        return {"error": "❌ مفتاح Gemini غير موجود"}

    prompt = f"""
    أنت HumanOS، خبير في تحليل المسارات المهنية.
    المستخدم: عمره {age}، يعمل كـ {job}، دخله {income}$، مهاراته: {skills}، هدفه: {goal}.

    قدّم 3 سيناريوهات مستقبلية مفصلة (JSON فقط):
    1. البقاء على الحال بعد 5 سنوات
    2. تطوير مهارة جديدة
    3. تغيير المهنة

    الشكل:
    {{
        "scenario_stay": {{"title": "البقاء على الحال", "description": "...", "income_after_5_years": "...", "satisfaction": "..."}},
        "scenario_learn": {{"title": "التطوير الذاتي", "description": "...", "skill_to_learn": "...", "income_after_5_years": "...", "satisfaction": "..."}},
        "scenario_change": {{"title": "التغيير الكامل", "description": "...", "new_career": "...", "income_after_5_years": "...", "satisfaction": "..."}}
    }}
    اللغة: {language}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            return {"error": f"❌ خطأ من Gemini (HTTP {response.status_code})"}
        
        data = response.json()
        if "candidates" not in data:
            return {"error": "❌ رد غير متوقع من Gemini"}
        
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]
        
        clean_text = text_response.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            return {"result": text_response}
            
    except Exception as e:
        return {"error": f"❌ خطأ: {str(e)}"}