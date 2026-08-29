import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ============================
# دوال الاتصال بـ Gemini (إصدارات حديثة)
# ============================

def call_gemini_pro_extended(prompt: str, max_tokens: int = 1000):
    """Gemini 3.1 Pro Extended - أقوى نموذج (حساب مدفوع)"""
    if not GEMINI_API_KEY:
        print("⚠️ مفتاح Gemini غير موجود")
        return None
    
    model = "gemini-3.1-pro-extended"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens,
            "topP": 0.95
        }
    }
    
    try:
        print(f"🔄 محاولة مع Gemini 3.1 Pro Extended (مدفوع)...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                print(f"✅ نجح Gemini 3.1 Pro Extended")
                return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print(f"⚠️ فشل Gemini Pro Extended: HTTP {response.status_code}")
            print(f"📄 الرد: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"⚠️ خطأ في Gemini Pro Extended: {e}")
        return None

def call_gemini_31_pro(prompt: str, max_tokens: int = 800):
    """Gemini 3.1 Pro - استدلال متقدم (حساب مدفوع)"""
    if not GEMINI_API_KEY:
        return None
    
    model = "gemini-3.1-pro"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        print(f"🔄 محاولة مع Gemini 3.1 Pro...")
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                print(f"✅ نجح Gemini 3.1 Pro")
                return data["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except:
        return None

def call_gemini_flash(prompt: str, max_tokens: int = 800):
    """Gemini 3.7 Flash - سريع وشامل"""
    if not GEMINI_API_KEY:
        return None
    
    model = "gemini-3.7-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        print(f"🔄 محاولة مع Gemini 3.7 Flash...")
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                print(f"✅ نجح Gemini 3.7 Flash")
                return data["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except:
        return None

def call_gemini_flash_lite(prompt: str, max_tokens: int = 600):
    """Gemini 3.5 Flash-Lite - الأسرع (احتياطي)"""
    if not GEMINI_API_KEY:
        return None
    
    model = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        print(f"🔄 محاولة مع Gemini 3.5 Flash-Lite...")
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                print(f"✅ نجح Gemini 3.5 Flash-Lite")
                return data["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except:
        return None

# ============================
# دوال الاتصال بـ DeepSeek (احتياطي)
# ============================

def call_deepseek(prompt: str, max_tokens: int = 800):
    """DeepSeek - احتياطي"""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        print(f"🔄 محاولة مع DeepSeek (احتياطي)...")
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ نجح DeepSeek")
            return data["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"⚠️ خطأ في DeepSeek: {e}")
        return None

# ============================
# الرد الافتراضي (Fallback)
# ============================

def generate_fallback_response(problem_text: str, language: str = "ar"):
    """رد افتراضي عند فشل جميع المحاولات"""
    return {
        "diagnosis": f"📌 تحليل مؤقت لمشكلتك: '{problem_text[:100]}...'\n(لم نتمكن من الاتصال بالذكاء الاصطناعي حالياً. هذا تحليل مبدئي.)",
        "gaps": "🔍 الفجوات المحتملة: تحتاج المشكلة إلى توضيح أكثر، أو أن خدمة الذكاء الاصطناعي غير متاحة حالياً.",
        "solutions": [
            "💡 حل 1: أعد صياغة مشكلتك بوضوح أكبر.",
            "💡 حل 2: تحقق من اتصال الإنترنت وأعد المحاولة.",
            "💡 حل 3: استخدم محاكي المستقبل للحصول على توجيه إضافي."
        ],
        "action_plan": "📋 خطة الأسبوع:\n1- أعد صياغة المشكلة.\n2- جرب الحلول المقترحة.\n3- عد للتطبيق غداً للمتابعة."
    }

# ============================
# استخراج البيانات من النص
# ============================

def extract_json_from_text(text: str):
    """محاولة استخراج البيانات من النص الخام"""
    try:
        return json.loads(text)
    except:
        pass
    
    result = {}
    sections = {
        "diagnosis": ["التشخيص", "diagnosis", "تحليل"],
        "gaps": ["الفجوات", "gaps", "الأسباب", "الثغرات"],
        "solutions": ["الحلول", "solutions", "حلول"],
        "action_plan": ["الخطة", "action_plan", "خطة", "خطة تنفيذية"]
    }
    
    lines = text.split('\n')
    current_section = None
    content = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for key, keywords in sections.items():
            for keyword in keywords:
                if keyword in line.lower() and any(c in line for c in [':', '-', '—']):
                    current_section = key
                    parts = re.split(r'[:—-]', line, 1)
                    if len(parts) > 1:
                        content[key] = parts[1].strip()
                    break
        if current_section and current_section not in content:
            if line and not any(k in line.lower() for keywords in sections.values() for k in keywords):
                content[current_section] = content.get(current_section, '') + ' ' + line
    
    for key in sections.keys():
        if key == "solutions":
            if key in content:
                solutions = [s.strip() for s in re.split(r'[،\n\d+\.]', content[key]) if s.strip()]
                result[key] = solutions if solutions else ["لا يوجد"]
            else:
                result[key] = ["لا يوجد"]
        else:
            result[key] = content.get(key, "لا يوجد")
    
    for key in sections.keys():
        if key not in result:
            result[key] = "لا يوجد" if key != "solutions" else ["لا يوجد"]
    
    return result

# ============================
# الدالة الرئيسية لحل المشكلة
# ============================

def solve_problem(problem_text: str, user_language: str = "ar"):
    print("="*60)
    print(f"📥 مشكلة: {problem_text[:50]}...")
    
    if not problem_text or len(problem_text.strip()) < 3:
        return {"error": "❌ المشكلة قصيرة جداً"}
    
    prompt = f"""
    أنت HumanOS، مستشار ذكي محترف.
    المستخدم قال: "{problem_text}"

    حلل المشكلة وقدّم إجابة عملية ومنظمة بهذا الشكل:
    التشخيص: (تحليل دقيق للمشكلة)
    الفجوات: (الأسباب الرئيسية)
    الحلول: (3 حلول عملية مرقمة)
    الخطة: (خطة تنفيذية للأسبوع القادم)

    اللغة: {user_language}
    قدم الإجابة بلغة عربية فصحى واضحة ومباشرة.
    """

    response_text = None

    # 1. المحاولة بـ Gemini 3.1 Pro Extended (الأقوى)
    if GEMINI_API_KEY:
        response_text = call_gemini_pro_extended(prompt)
    
    # 2. إذا فشل، نحاول بـ Gemini 3.1 Pro
    if not response_text and GEMINI_API_KEY:
        response_text = call_gemini_31_pro(prompt)
    
    # 3. إذا فشل، نحاول بـ Gemini 3.7 Flash
    if not response_text and GEMINI_API_KEY:
        response_text = call_gemini_flash(prompt)
    
    # 4. إذا فشل، نحاول بـ Gemini 3.5 Flash-Lite
    if not response_text and GEMINI_API_KEY:
        response_text = call_gemini_flash_lite(prompt)
    
    # 5. إذا فشل، نحاول بـ DeepSeek
    if not response_text and DEEPSEEK_API_KEY:
        response_text = call_deepseek(prompt)
    
    # 6. إذا فشل كل شيء، نستعمل الرد الافتراضي
    if not response_text:
        print("⚠️ جميع APIs فشلت، نستعمل الرد الافتراضي")
        return generate_fallback_response(problem_text, user_language)
    
    print(f"📝 الرد: {response_text[:200]}...")
    
    result = extract_json_from_text(response_text)
    
    required_keys = ["diagnosis", "gaps", "solutions", "action_plan"]
    for key in required_keys:
        if key not in result or not result[key]:
            result[key] = "لا يوجد" if key != "solutions" else ["لا يوجد"]
    
    return result

# ============================
# محاكي المستقبل
# ============================

def simulate_future(age: int, job: str, income: float, skills: str, goal: str, language: str = "ar"):
    print("="*60)
    print(f"🔮 محاكي المستقبل: العمر {age}, الوظيفة {job}")
    
    if not all([age, job, income, skills]):
        return {"error": "❌ جميع الحقول مطلوبة"}
    
    prompt = f"""
    أنت HumanOS، خبير في تحليل المسارات المهنية.
    المستخدم: عمره {age}، يعمل كـ {job}، دخله {income}$، مهاراته: {skills}، هدفه: {goal}.

    قدّم 3 سيناريوهات مستقبلية مفصلة:
    1. البقاء على الحال بعد 5 سنوات
    2. تطوير مهارة جديدة
    3. تغيير المهنة

    الشكل المطلوب:
    سيناريو 1: البقاء على الحال - وصف مفصل - الدخل المتوقع - مستوى الرضا
    سيناريو 2: التطوير الذاتي - وصف مفصل - المهارة المقترحة - الدخل المتوقع - مستوى الرضا
    سيناريو 3: التغيير الكامل - وصف مفصل - المهنة الجديدة - الدخل المتوقع - مستوى الرضا

    اللغة: {language}
    """

    response_text = None

    # 1. Gemini 3.1 Pro Extended
    if GEMINI_API_KEY:
        response_text = call_gemini_pro_extended(prompt, max_tokens=1000)
    
    # 2. Gemini 3.1 Pro
    if not response_text and GEMINI_API_KEY:
        response_text = call_gemini_31_pro(prompt, max_tokens=800)
    
    # 3. Gemini 3.7 Flash
    if not response_text and GEMINI_API_KEY:
        response_text = call_gemini_flash(prompt, max_tokens=800)
    
    # 4. DeepSeek
    if not response_text and DEEPSEEK_API_KEY:
        response_text = call_deepseek(prompt, max_tokens=800)
    
    # إذا فشل كل شيء، نستعمل رداً افتراضياً
    if not response_text:
        return {
            "scenario_stay": {
                "title": "البقاء على الحال",
                "description": f"إذا بقيت في وظيفتك الحالية ({job})، من المتوقع استقرار الدخل عند {income}$ مع تطور محدود.",
                "income_after_5_years": f"${income * 1.15:.0f} شهرياً",
                "satisfaction": "متوسطة"
            },
            "scenario_learn": {
                "title": "التطوير الذاتي",
                "description": f"بإتقان مهارات متقدمة في {skills.split(',')[0] if skills else 'مجالك'}، ستتوسع فرصك المهنية.",
                "skill_to_learn": skills.split(',')[0].strip() if skills else "مهارات متقدمة",
                "income_after_5_years": f"${income * 1.7:.0f} شهرياً",
                "satisfaction": "عالية"
            },
            "scenario_change": {
                "title": "التغيير الكامل",
                "description": "الانتقال لمجال جديد قد يكون صعباً في البداية ولكنه يحمل إمكانيات كبيرة.",
                "new_career": "مجال التكنولوجيا أو الإدارة",
                "income_after_5_years": f"${income * 2.2:.0f} شهرياً",
                "satisfaction": "عالية جداً"
            }
        }
    
    # استخراج السيناريوهات
    result = {}
    scenarios = []
    lines = response_text.split('\n')
    current = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "سيناريو 1" in line or "بقاء" in line:
            if current: scenarios.append(current)
            current = {"title": line}
        elif "سيناريو 2" in line or "تطوير" in line:
            if current: scenarios.append(current)
            current = {"title": line}
        elif "سيناريو 3" in line or "تغيير" in line:
            if current: scenarios.append(current)
            current = {"title": line}
        elif current:
            parts = line.split(':', 1) if ':' in line else [line]
            if len(parts) > 1:
                key = parts[0].strip().lower()
                value = parts[1].strip()
                if "وصف" in key:
                    current["description"] = value
                elif "دخل" in key or "income" in key:
                    current["income_after_5_years"] = value
                elif "رضا" in key or "satisfaction" in key:
                    current["satisfaction"] = value
                elif "مهارة" in key or "skill" in key:
                    current["skill_to_learn"] = value
                elif "مهنة" in key or "career" in key:
                    current["new_career"] = value
    
    if current:
        scenarios.append(current)
    
    if len(scenarios) >= 3:
        result = {
            "scenario_stay": {
                "title": scenarios[0].get("title", "البقاء على الحال"),
                "description": scenarios[0].get("description", "لا يوجد وصف"),
                "income_after_5_years": scenarios[0].get("income_after_5_years", "غير محدد"),
                "satisfaction": scenarios[0].get("satisfaction", "غير محدد")
            },
            "scenario_learn": {
                "title": scenarios[1].get("title", "التطوير الذاتي"),
                "description": scenarios[1].get("description", "لا يوجد وصف"),
                "skill_to_learn": scenarios[1].get("skill_to_learn", "غير محدد"),
                "income_after_5_years": scenarios[1].get("income_after_5_years", "غير محدد"),
                "satisfaction": scenarios[1].get("satisfaction", "غير محدد")
            },
            "scenario_change": {
                "title": scenarios[2].get("title", "التغيير الكامل"),
                "description": scenarios[2].get("description", "لا يوجد وصف"),
                "new_career": scenarios[2].get("new_career", "غير محدد"),
                "income_after_5_years": scenarios[2].get("income_after_5_years", "غير محدد"),
                "satisfaction": scenarios[2].get("satisfaction", "غير محدد")
            }
        }
    else:
        result = {
            "scenario_stay": {
                "title": "البقاء على الحال",
                "description": response_text[:200],
                "income_after_5_years": "غير محدد",
                "satisfaction": "غير محدد"
            },
            "scenario_learn": {
                "title": "التطوير الذاتي",
                "description": response_text[200:400] if len(response_text) > 200 else response_text,
                "skill_to_learn": "غير محدد",
                "income_after_5_years": "غير محدد",
                "satisfaction": "غير محدد"
            },
            "scenario_change": {
                "title": "التغيير الكامل",
                "description": "انظر التفاصيل أعلاه",
                "new_career": "غير محدد",
                "income_after_5_years": "غير محدد",
                "satisfaction": "غير محدد"
            }
        }
    
    return result