from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ai_gateway import solve_problem, simulate_future
from humanos.db.session import get_db, engine, Base
from humanos.models import user
from humanos.models.solution import Solution
from humanos.api.v1 import auth
import json

# ===== إنشاء الجداول =====
Base.metadata.create_all(bind=engine)

# ===== تعريف التطبيق =====
app = FastAPI(title="HumanOS Core", version="1.0.0")

# ===== تضمين مسارات المصادقة =====
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# ===== المسارات الأساسية =====
@app.get("/")
def read_root():
    return {"message": "مرحبا بك في HumanOS!"}

@app.get("/health")
def health_check():
    return {"status": "alive", "db": "sqlite"}

# ===== حل المشكلة =====
class ProblemRequest(BaseModel):
    user_id: int
    problem: str
    language: str = "ar"

@app.post("/solve")
def solve(problem_req: ProblemRequest, db: Session = Depends(get_db)):
    ai_result = solve_problem(problem_req.problem, problem_req.language)
    
    diagnosis = ai_result.get("diagnosis")
    gaps = ai_result.get("gaps")
    solutions_list = ai_result.get("solutions")
    action_plan = ai_result.get("action_plan")
    solutions_json = json.dumps(solutions_list) if solutions_list else None

    new_solution = Solution(
        user_id=problem_req.user_id,
        problem=problem_req.problem,
        diagnosis=diagnosis,
        gaps=gaps,
        solutions=solutions_json,
        action_plan=action_plan
    )
    db.add(new_solution)
    db.commit()
    db.refresh(new_solution)

    return {
        "solution_id": new_solution.id,
        "diagnosis": diagnosis,
        "gaps": gaps,
        "solutions": solutions_list,
        "action_plan": action_plan
    }

# ===== التاريخ =====
@app.get("/history/{user_id}")
def get_history(user_id: int, db: Session = Depends(get_db)):
    solutions = db.query(Solution).filter(Solution.user_id == user_id).order_by(Solution.created_at.desc()).limit(10).all()
    if not solutions:
        return {"message": "مازال ما عندكش تحليلات", "history": []}
    history_list = []
    for sol in solutions:
        history_list.append({
            "id": sol.id,
            "problem": sol.problem,
            "diagnosis": sol.diagnosis,
            "gaps": sol.gaps,
            "action_plan": sol.action_plan,
            "created_at": sol.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return {"user_id": user_id, "count": len(history_list), "history": history_list}

# ===== محاكي المستقبل =====
class SimulateRequest(BaseModel):
    user_id: int
    age: int
    job: str
    income: float
    skills: str
    goal: str = "تحسين الوضع المهني"
    language: str = "ar"

@app.post("/simulate")
def simulate(request: SimulateRequest, db: Session = Depends(get_db)):
    result = simulate_future(
        age=request.age,
        job=request.job,
        income=request.income,
        skills=request.skills,
        goal=request.goal,
        language=request.language
    )
    return result

# ===== الملف الشخصي =====
class ProfileUpdate(BaseModel):
    user_id: int
    full_name: str
    age: int
    job_title: str
    monthly_income: float
    skills: str

@app.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(user.User).filter(user.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "full_name": db_user.full_name,
        "email": db_user.email,
        "age": db_user.age,
        "job_title": db_user.job_title,
        "monthly_income": db_user.monthly_income,
        "skills": db_user.skills
    }

@app.post("/profile/update")
def update_profile(profile: ProfileUpdate, db: Session = Depends(get_db)):
    db_user = db.query(user.User).filter(user.User.id == profile.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.full_name = profile.full_name
    db_user.age = profile.age
    db_user.job_title = profile.job_title
    db_user.monthly_income = profile.monthly_income
    db_user.skills = profile.skills
    db.commit()
    db.refresh(db_user)
    return {"message": "Profile updated successfully"}

# ===== لوحة التحكم =====
@app.get("/api/dashboard/stats/{user_id}")
def dashboard_stats(user_id: int, db: Session = Depends(get_db)):
    total_solutions = db.query(Solution).filter(Solution.user_id == user_id).count()
    recent = db.query(Solution).filter(Solution.user_id == user_id).order_by(Solution.created_at.desc()).limit(5).all()
    recent_list = [{"problem": s.problem, "created_at": s.created_at.strftime("%Y-%m-%d %H:%M")} for s in recent]
    return {"total_solutions": total_solutions, "recent": recent_list}

# ===== تقرير PDF =====
@app.get("/report/{solution_id}", response_class=HTMLResponse)
def report_frontend(solution_id: int, db: Session = Depends(get_db)):
    sol = db.query(Solution).filter(Solution.id == solution_id).first()
    if not sol:
        return "<h1>التقرير غير موجود</h1>"
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>تقرير HumanOS</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; direction: rtl; background: white; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .section {{ background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        button {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
        @media print {{ .no-print {{ display: none; }} body {{ margin: 0; padding: 10px; }} }}
    </style>
    </head>
    <body>
        <h1>🧠 تقرير HumanOS</h1>
        <p><strong>📅 التاريخ:</strong> {sol.created_at.strftime("%Y-%m-%d %H:%M")}</p>
        <div class="section"><div class="label">❓ المشكلة:</div><p>{sol.problem}</p></div>
        <div class="section"><div class="label">📋 التشخيص:</div><p>{sol.diagnosis or "لا يوجد"}</p></div>
        <div class="section"><div class="label">🔍 الفجوات:</div><p>{sol.gaps or "لا يوجد"}</p></div>
        <div class="section"><div class="label">💡 الحلول:</div><p>{sol.solutions or "لا يوجد"}</p></div>
        <div class="section"><div class="label">🗓️ الخطة:</div><p>{sol.action_plan or "لا يوجد"}</p></div>
        <button class="no-print" onclick="window.print()">🖨️ طباعة / حفظ كـ PDF</button>
        <br><br><a href="/app" class="no-print">⬅️ الرجوع للرئيسية</a>
    </body>
    </html>
    """

# ==========================================
# ===== صفحة التاريخ (HTML) =====
@app.get("/history-view/{user_id}", response_class=HTMLResponse)
def history_frontend(user_id: int):
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>تاريخي - HumanOS</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; direction: rtl; background: #f5f5f5; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        h1 {{ color: #333; }}
        .problem {{ font-weight: bold; color: #1a237e; }}
        .meta {{ font-size: 12px; color: #888; }}
        .diagnosis {{ background: #e3f2fd; padding: 10px; border-radius: 8px; margin: 8px 0; }}
        .plan {{ background: #e8f5e9; padding: 10px; border-radius: 8px; margin: 8px 0; }}
        .back {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 8px; }}
        .empty {{ text-align: center; color: #888; padding: 40px; }}
    </style>
    </head>
    <body>
        <div class="card">
            <h1>📜 تاريخ تحليلاتي</h1>
            <div id="history-container"><p>⏳ جاري التحميل...</p></div>
            <a href="/app" class="back">⬅️ الرجوع للرئيسية</a>
        </div>
        <script>
            fetch('/history/{user_id}')
                .then(res => res.json())
                .then(data => {{
                    const container = document.getElementById('history-container');
                    if (data.history && data.history.length > 0) {{
                        let html = '';
                        data.history.forEach(item => {{
                            html += `
                                <div class="card">
                                    <div class="problem">❓ ${{item.problem}}</div>
                                    <div class="meta">📅 ${{item.created_at}}</div>
                                    <div class="diagnosis">📋 <strong>التشخيص:</strong> ${{item.diagnosis || 'لا يوجد'}}</div>
                                    <div><strong>🔍 الفجوات:</strong> ${{item.gaps || 'لا يوجد'}}</div>
                                    <div class="plan">🗓️ <strong>الخطة:</strong> ${{item.action_plan || 'لا يوجد'}}</div>
                                    <a href="/report/${{item.id}}" target="_blank" style="display:inline-block; margin-top:10px; background:#FF9800; color:white; padding:5px 15px; border-radius:5px; text-decoration:none;">📄 تحميل التقرير</a>
                                </div>
                            `;
                        }});
                        container.innerHTML = html;
                    }} else {{
                        container.innerHTML = `<div class="empty">📭 مازال ما عندكش تحليلات.</div>`;
                    }}
                }})
                .catch(err => {{
                    document.getElementById('history-container').innerHTML = `<div class="empty">❌ خطأ في التحميل: ${{err.message}}</div>`;
                }});
        </script>
    </body>
    </html>
    """

# ==========================================
# ===== صفحة الملف الشخصي (HTML) =====
@app.get("/profile-view/{user_id}", response_class=HTMLResponse)
def profile_frontend(user_id: int):
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>ملفي الشخصي - HumanOS</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; direction: rtl; background: #f5f5f5; }}
        .card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        input {{ width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }}
        button {{ background: #4CAF50; color: white; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; }}
        .back {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #2196F3; color: white; text-decoration: none; border-radius: 8px; }}
        .success {{ background: #e8f5e9; color: #2e7d32; padding: 10px; border-radius: 8px; }}
        .error {{ background: #ffebee; color: #c62828; padding: 10px; border-radius: 8px; }}
    </style>
    </head>
    <body>
        <div class="card">
            <h1>👤 ملفي الشخصي</h1>
            <div id="profile-form">
                <input type="text" id="p-name" placeholder="الاسم الكامل">
                <input type="number" id="p-age" placeholder="العمر">
                <input type="text" id="p-job" placeholder="الوظيفة الحالية">
                <input type="number" id="p-income" placeholder="الدخل الشهري">
                <input type="text" id="p-skills" placeholder="المهارات (مفصولة بفواصل)">
                <button onclick="updateProfile()">💾 حفظ الملف الشخصي</button>
                <div id="profile-msg"></div>
            </div>
            <a href="/app" class="back">⬅️ الرجوع للرئيسية</a>
        </div>
        <script>
            fetch('/profile/{user_id}')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('p-name').value = data.full_name || '';
                    document.getElementById('p-age').value = data.age || '';
                    document.getElementById('p-job').value = data.job_title || '';
                    document.getElementById('p-income').value = data.monthly_income || '';
                    document.getElementById('p-skills').value = data.skills || '';
                }}).catch(err => console.log(err));
            async function updateProfile() {{
                const user_id = {user_id};
                const full_name = document.getElementById('p-name').value;
                const age = document.getElementById('p-age').value;
                const job_title = document.getElementById('p-job').value;
                const monthly_income = document.getElementById('p-income').value;
                const skills = document.getElementById('p-skills').value;
                const msg = document.getElementById('profile-msg');
                if (!full_name) {{ msg.innerHTML = '<div class="error">⚠️ الاسم مطلوب</div>'; return; }}
                try {{
                    const res = await fetch('/profile/update', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ user_id: parseInt(user_id), full_name, age: parseInt(age), job_title, monthly_income: parseFloat(monthly_income), skills }})
                    }});
                    const data = await res.json();
                    if (res.ok) {{
                        msg.innerHTML = '<div class="success">✅ تم حفظ الملف الشخصي!</div>';
                    }} else {{
                        msg.innerHTML = `<div class="error">❌ ${{data.detail || 'خطأ'}}</div>`;
                    }}
                }} catch (e) {{
                    msg.innerHTML = `<div class="error">❌ خطأ في الاتصال: ${{e.message}}</div>`;
                }}
            }}
        </script>
    </body>
    </html>
    """

# ==========================================
# ===== صفحة لوحة التحكم (HTML) =====
@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard_frontend(user_id: int):
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>لوحة التحكم - HumanOS</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; direction: rtl; background: #f5f5f5; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        h1 {{ color: #333; }}
        .stat {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .back {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 8px; }}
        .recent-item {{ padding: 8px; border-bottom: 1px solid #eee; }}
    </style>
    </head>
    <body>
        <div class="card">
            <h1>📊 لوحة التحكم</h1>
            <div id="stats-container"><p>⏳ جاري التحميل...</p></div>
            <a href="/app" class="back">⬅️ الرجوع للرئيسية</a>
        </div>
        <script>
            fetch('/api/dashboard/stats/{user_id}')
                .then(res => res.json())
                .then(data => {{
                    const container = document.getElementById('stats-container');
                    let html = `<p>📌 <strong>إجمالي المشاكل المحلولة:</strong> <span class="stat">${{data.total_solutions}}</span></p>`;
                    html += `<h3>🕒 آخر 5 مشاكل:</h3>`;
                    if (data.recent && data.recent.length > 0) {{
                        data.recent.forEach(item => {{
                            html += `<div class="recent-item">📅 ${{item.created_at}} - ❓ ${{item.problem}}</div>`;
                        }});
                    }} else {{
                        html += `<p>لا توجد مشاكل بعد.</p>`;
                    }}
                    container.innerHTML = html;
                }})
                .catch(err => {{
                    document.getElementById('stats-container').innerHTML = `<p class="error">❌ خطأ في التحميل: ${{err.message}}</p>`;
                }});
        </script>
    </body>
    </html>
    """

# ==========================================
# ===== الواجهة الرئيسية الجديدة (Glassmorphism) =====
@app.get("/app", response_class=HTMLResponse)
def frontend():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HumanOS - نظام تشغيل الحياة</title>
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Tajawal', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                direction: rtl;
            }
            .glass-card {
                background: rgba(255, 255, 255, 0.15);
                backdrop-filter: blur(15px);
                -webkit-backdrop-filter: blur(15px);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                box-shadow: 0 30px 50px rgba(0, 0, 0, 0.3);
                padding: 30px;
                max-width: 650px;
                width: 100%;
                transition: all 0.3s ease;
            }
            h1 {
                font-size: 32px;
                font-weight: 800;
                color: #fff;
                text-shadow: 0 4px 15px rgba(0,0,0,0.2);
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .subtitle {
                color: rgba(255,255,255,0.8);
                font-size: 14px;
                margin-bottom: 25px;
                border-right: 3px solid rgba(255,255,255,0.4);
                padding-right: 12px;
            }
            .tab-group {
                display: flex;
                background: rgba(0,0,0,0.2);
                border-radius: 15px;
                padding: 4px;
                margin-bottom: 25px;
            }
            .tab {
                flex: 1;
                text-align: center;
                padding: 10px 5px;
                border-radius: 12px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s;
                color: rgba(255,255,255,0.6);
                font-size: 15px;
            }
            .tab.active {
                background: rgba(255,255,255,0.95);
                color: #5a3d8a;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .tab-content { display: none; animation: fade 0.3s ease; }
            .tab-content.active { display: block; }
            @keyframes fade { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            
            .input-group {
                margin-bottom: 15px;
                position: relative;
            }
            .input-group label {
                display: block;
                color: rgba(255,255,255,0.8);
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 5px;
                padding-right: 5px;
            }
            .input-group input, .input-group textarea {
                width: 100%;
                padding: 12px 18px;
                border: none;
                border-radius: 14px;
                background: rgba(255,255,255,0.9);
                font-size: 16px;
                font-family: 'Tajawal', sans-serif;
                transition: all 0.2s;
                color: #333;
            }
            .input-group input:focus, .input-group textarea:focus {
                outline: none;
                box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.4);
                background: #ffffff;
            }
            .input-group textarea { min-height: 100px; resize: vertical; }
            
            .btn {
                width: 100%;
                padding: 14px;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: 700;
                font-family: 'Tajawal', sans-serif;
                cursor: pointer;
                transition: all 0.3s ease;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
            }
            .btn:hover { transform: scale(1.02); box-shadow: 0 10px 25px rgba(102, 126, 234, 0.5); }
            .btn-secondary { background: rgba(255,255,255,0.2); backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.3); }
            .btn-secondary:hover { background: rgba(255,255,255,0.3); }
            .btn-purple { background: linear-gradient(135deg, #f093fb, #f5576c); box-shadow: 0 8px 20px rgba(245, 87, 108, 0.3); }
            .btn-purple:hover { box-shadow: 0 10px 25px rgba(245, 87, 108, 0.5); }
            
            .message-box { margin-top: 15px; padding: 12px; border-radius: 12px; font-weight: 500; display: none; }
            .error { background: rgba(255, 0, 0, 0.15); color: #fff; border: 1px solid rgba(255, 0, 0, 0.2); display: block; }
            .success { background: rgba(0, 255, 0, 0.15); color: #fff; border: 1px solid rgba(0, 255, 0, 0.2); display: block; }
            .info-box { background: rgba(255,255,255,0.1); border-radius: 14px; padding: 15px; margin: 15px 0; backdrop-filter: blur(5px); border: 1px solid rgba(255,255,255,0.1); }
            
            .user-nav { display: flex; gap: 10px; flex-wrap: wrap; margin: 15px 0; }
            .nav-btn {
                padding: 8px 18px;
                background: rgba(255,255,255,0.15);
                border-radius: 30px;
                color: white;
                text-decoration: none;
                font-weight: 500;
                font-size: 14px;
                transition: 0.2s;
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(5px);
                cursor: pointer;
            }
            .nav-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
            .nav-btn.logout { background: rgba(255, 50, 50, 0.3); border-color: rgba(255,50,50,0.2); }
            
            .result-box { background: rgba(0,0,0,0.2); border-radius: 14px; padding: 20px; margin-top: 20px; color: #fff; }
            .result-box .label { font-weight: 700; color: #f3e8ff; margin-top: 12px; margin-bottom: 5px; display: block; }
            .result-box ul { padding-right: 20px; margin: 8px 0; }
            .result-box li { margin-bottom: 5px; }
            
            .sim-section { background: rgba(255,255,255,0.05); border-radius: 14px; padding: 15px; margin-top: 15px; border: 1px dashed rgba(255,255,255,0.2); display: none; }
            .sim-section h3 { color: #fff; margin-bottom: 10px; }
            
            .scenario-card { background: rgba(255,255,255,0.08); border-radius: 12px; padding: 15px; margin: 10px 0; border-right: 4px solid #f5576c; }
            .scenario-card h5 { color: #fff; font-size: 16px; }
            
            hr { border: 1px solid rgba(255,255,255,0.1); margin: 20px 0; }
            .flex-row { display: flex; gap: 10px; }
            .flex-row .btn { width: auto; padding: 10px 25px; }
            
            @media (max-width: 500px) { .glass-card { padding: 20px; } h1 { font-size: 26px; } }
        </style>
    </head>
    <body>
        <div class="glass-card">
            <h1>🧠 HumanOS</h1>
            <div class="subtitle">نظام تشغيل الحياة بالذكاء الاصطناعي</div>

            <!-- ========== قسم المصادقة ========== -->
            <div id="auth-section">
                <div class="tab-group">
                    <span class="tab active" onclick="switchTab('login')" id="login-tab">🔐 دخول</span>
                    <span class="tab" onclick="switchTab('register')" id="register-tab">📝 تسجيل</span>
                </div>

                <!-- تسجيل -->
                <div id="register-form" class="tab-content">
                    <h3 style="color:#fff; margin-bottom:15px;">🌟 إنشاء حساب جديد</h3>
                    <div class="input-group">
                        <label>👤 الاسم الكامل</label>
                        <input type="text" id="reg-name" placeholder="مصطفى الغالي">
                    </div>
                    <div class="input-group">
                        <label>📧 البريد الإلكتروني</label>
                        <input type="email" id="reg-email" placeholder="example@email.com">
                    </div>
                    <div class="input-group">
                        <label>🔒 كلمة السر</label>
                        <input type="password" id="reg-password" placeholder="أدخل كلمة سر قوية">
                    </div>
                    <button class="btn" onclick="registerUser()">🚀 تسجيل</button>
                    <div id="reg-message" class="message-box"></div>
                </div>

                <!-- دخول -->
                <div id="login-form" class="tab-content active">
                    <h3 style="color:#fff; margin-bottom:15px;">🔐 دخول إلى حسابك</h3>
                    <div class="input-group">
                        <label>📧 البريد الإلكتروني</label>
                        <input type="email" id="login-email" placeholder="example@email.com">
                    </div>
                    <div class="input-group">
                        <label>🔒 كلمة السر</label>
                        <input type="password" id="login-password" placeholder="أدخل كلمة السر">
                    </div>
                    <button class="btn" onclick="loginUser()">🚀 دخول</button>
                    <div id="login-message" class="message-box"></div>
                </div>
            </div>

            <!-- ========== قسم حل المشاكل ========== -->
            <div id="solve-section" style="display:none;">
                <div class="info-box" id="user-info-display">
                    👤 مرحباً بك في HumanOS
                </div>
                
                <div class="user-nav">
                    <span class="nav-btn" onclick="viewProfile()">👤 ملفي الشخصي</span>
                    <span class="nav-btn" onclick="viewDashboard()">📊 لوحة التحكم</span>
                    <span class="nav-btn" onclick="viewHistory()">📜 التاريخ</span>
                    <span class="nav-btn logout" onclick="logout()">🚪 خروج</span>
                </div>

                <hr>
                
                <div class="input-group">
                    <label for="problem">✍️ أخبرني مشكلتك:</label>
                    <textarea id="problem" placeholder="مثلاً: أنا عاطل وعندي خبرة 3 سنوات في بايثون..."></textarea>
                </div>
                <button class="btn" onclick="solveProblem()">🧠 حل المشكلة</button>
                
                <div id="result" class="result-box" style="display:none;"></div>

                <hr>
                <button class="btn btn-secondary" onclick="toggleSimulator()">🔮 محاكي المستقبل (سيناريوهات)</button>
                
                <div id="simulator-section" class="sim-section">
                    <h3>🔮 أدخل بياناتك</h3>
                    <div class="input-group"><label>العمر</label><input type="number" id="sim-age" value="30"></div>
                    <div class="input-group"><label>الوظيفة الحالية</label><input type="text" id="sim-job" value="مبرمج بايثون"></div>
                    <div class="input-group"><label>الدخل الشهري ($)</label><input type="number" id="sim-income" value="1000"></div>
                    <div class="input-group"><label>المهارات</label><input type="text" id="sim-skills" value="Python, Django"></div>
                    <div class="input-group"><label>الهدف</label><input type="text" id="sim-goal" value="تحسين الوضع المهني"></div>
                    <button class="btn btn-purple" onclick="simulateFuture()">🚀 احسب سيناريوهاتي</button>
                    <div id="sim-result" style="margin-top:15px; color:#fff;"></div>
                </div>
            </div>
        </div>

        <script>
            // ===== JavaScript =====
            let currentUserId = null;
            let currentEmail = null;

            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                if (tab === 'login') {
                    document.getElementById('login-tab').classList.add('active');
                    document.getElementById('login-form').classList.add('active');
                } else {
                    document.getElementById('register-tab').classList.add('active');
                    document.getElementById('register-form').classList.add('active');
                }
            }

            function showMessage(element, text, type) {
                element.innerHTML = text;
                element.className = 'message-box ' + type;
                element.style.display = 'block';
            }

            async function registerUser() {
                const name = document.getElementById('reg-name').value;
                const email = document.getElementById('reg-email').value;
                const password = document.getElementById('reg-password').value;
                const msg = document.getElementById('reg-message');
                if (!name || !email || !password) { showMessage(msg, '⚠️ جميع الحقول مطلوبة', 'error'); return; }
                try {
                    const res = await fetch('/api/v1/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ full_name: name, email: email, password: password })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        showMessage(msg, '✅ تم التسجيل! يمكنك الآن الدخول.', 'success');
                        switchTab('login');
                    } else {
                        showMessage(msg, '❌ ' + (data.detail || 'خطأ'), 'error');
                    }
                } catch (e) {
                    showMessage(msg, '❌ خطأ في الاتصال: ' + e.message, 'error');
                }
            }

            async function loginUser() {
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                const msg = document.getElementById('login-message');
                if (!email || !password) { showMessage(msg, '⚠️ جميع الحقول مطلوبة', 'error'); return; }
                try {
                    const res = await fetch('/api/v1/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: email, password: password })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        localStorage.setItem('user_id', data.user_id);
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('user_email', email);
                        currentUserId = data.user_id;
                        currentEmail = email;
                        showSolveSection(email);
                        showMessage(msg, '✅ تم الدخول بنجاح!', 'success');
                    } else {
                        showMessage(msg, '❌ ' + (data.detail || 'خطأ في البريد أو كلمة السر'), 'error');
                    }
                } catch (e) {
                    showMessage(msg, '❌ خطأ في الاتصال: ' + e.message, 'error');
                }
            }

            function showSolveSection(email) {
                document.getElementById('auth-section').style.display = 'none';
                document.getElementById('solve-section').style.display = 'block';
                fetch(`/profile/${localStorage.getItem('user_id')}`)
                    .then(res => res.json())
                    .then(data => {
                        const name = data.full_name || email;
                        document.getElementById('user-info-display').innerHTML = `👤 مرحباً، ${name}`;
                    })
                    .catch(() => {
                        document.getElementById('user-info-display').innerHTML = `👤 مرحباً، ${email}`;
                    });
            }

            window.onload = function() {
                const userId = localStorage.getItem('user_id');
                const email = localStorage.getItem('user_email');
                if (userId && email) {
                    currentUserId = userId;
                    currentEmail = email;
                    showSolveSection(email);
                }
            };

            async function solveProblem() {
                const user_id = localStorage.getItem('user_id');
                const problem = document.getElementById('problem').value;
                const resultDiv = document.getElementById('result');
                if (!user_id) { alert('الرجاء تسجيل الدخول أولاً'); return; }
                if (!problem) { resultDiv.innerHTML = '<div class="label">⚠️ من فضلك اكتب مشكلتك</div>'; resultDiv.style.display = 'block'; return; }
                resultDiv.innerHTML = '🧠 جاري التفكير...';
                resultDiv.style.display = 'block';
                try {
                    const res = await fetch('/solve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: parseInt(user_id), problem, language: 'ar' })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        let html = '<span class="label">📋 التشخيص</span><p>' + (data.diagnosis || 'لا يوجد') + '</p>';
                        html += '<span class="label">🔍 الفجوات</span><p>' + (data.gaps || 'لا يوجد') + '</p>';
                        html += '<span class="label">💡 الحلول المقترحة</span>';
                        if (data.solutions && data.solutions.length) {
                            html += '<ul>';
                            data.solutions.forEach(s => html += '<li>' + s + '</li>');
                            html += '</ul>';
                        } else { html += '<p>لا يوجد</p>'; }
                        html += '<span class="label">🗓️ الخطة التنفيذية</span><p>' + (data.action_plan || 'لا يوجد') + '</p>';
                        html += `<div style="margin-top:15px;"><a href="/report/${data.solution_id}" target="_blank" class="nav-btn" style="background:#f5576c; padding:8px 20px;">📄 تحميل التقرير (PDF)</a></div>`;
                        resultDiv.innerHTML = html;
                        resultDiv.style.display = 'block';
                    } else {
                        resultDiv.innerHTML = '<div class="label">❌ خطأ: ' + (data.error || 'غير معروف') + '</div>';
                        resultDiv.style.display = 'block';
                    }
                } catch (e) {
                    resultDiv.innerHTML = '<div class="label">❌ تعذر الاتصال بالخادم.</div>';
                    resultDiv.style.display = 'block';
                }
            }

            function viewHistory() {
                const id = localStorage.getItem('user_id');
                if (id) window.location.href = `/history-view/${id}`;
                else alert('سجل دخولك أولاً');
            }
            function viewProfile() {
                const id = localStorage.getItem('user_id');
                if (id) window.location.href = `/profile-view/${id}`;
                else alert('سجل دخولك أولاً');
            }
            function viewDashboard() {
                const id = localStorage.getItem('user_id');
                if (id) window.location.href = `/dashboard/${id}`;
                else alert('سجل دخولك أولاً');
            }
            function logout() { localStorage.clear(); window.location.reload(); }

            function toggleSimulator() {
                const el = document.getElementById('simulator-section');
                el.style.display = el.style.display === 'none' ? 'block' : 'none';
            }

            async function simulateFuture() {
                const user_id = localStorage.getItem('user_id');
                const age = document.getElementById('sim-age').value;
                const job = document.getElementById('sim-job').value;
                const income = document.getElementById('sim-income').value;
                const skills = document.getElementById('sim-skills').value;
                const goal = document.getElementById('sim-goal').value;
                const resultDiv = document.getElementById('sim-result');
                if (!user_id) { alert('سجل دخولك أولاً'); return; }
                resultDiv.innerHTML = '🧠 جاري حساب السيناريوهات...';
                try {
                    const res = await fetch('/simulate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: parseInt(user_id), age: parseInt(age), job, income: parseFloat(income), skills, goal, language: 'ar' })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        let html = '<h4 style="color:#fff;">📊 سيناريوهاتك المستقبلية</h4>';
                        if (data.scenario_stay) html += `<div class="scenario-card"><h5>🔵 ${data.scenario_stay.title}</h5><p>${data.scenario_stay.description}</p><p><strong>الدخل:</strong> ${data.scenario_stay.income_after_5_years}</p><p><strong>الرضا:</strong> ${data.scenario_stay.satisfaction}</p></div>`;
                        if (data.scenario_learn) html += `<div class="scenario-card" style="border-right-color:#f093fb;"><h5>🟠 ${data.scenario_learn.title}</h5><p>${data.scenario_learn.description}</p><p><strong>المهارة:</strong> ${data.scenario_learn.skill_to_learn}</p><p><strong>الدخل:</strong> ${data.scenario_learn.income_after_5_years}</p><p><strong>الرضا:</strong> ${data.scenario_learn.satisfaction}</p></div>`;
                        if (data.scenario_change) html += `<div class="scenario-card" style="border-right-color:#4ade80;"><h5>🟢 ${data.scenario_change.title}</h5><p>${data.scenario_change.description}</p><p><strong>المهنة الجديدة:</strong> ${data.scenario_change.new_career}</p><p><strong>الدخل:</strong> ${data.scenario_change.income_after_5_years}</p><p><strong>الرضا:</strong> ${data.scenario_change.satisfaction}</p></div>`;
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = '<div class="error">❌ خطأ: ' + (data.error || 'غير معروف') + '</div>';
                    }
                } catch (e) {
                    resultDiv.innerHTML = '<div class="error">❌ خطأ في الاتصال: ' + e.message + '</div>';
                }
            }
        </script>
    </body>
    </html>
    """