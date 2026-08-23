from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ai_gateway import solve_problem, simulate_future
from humanos.db.session import get_db, engine, Base
from humanos.models import user
from humanos.models.solution import Solution
from humanos.api.v1 import auth
import json
import os

# ننشئ الجداول
Base.metadata.create_all(bind=engine)

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

# ===== نموذج حل المشكلة =====
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

# ===== جلب التاريخ =====
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

# ===== نموذج محاكي المستقبل =====
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

# ==========================================
# ===== الخيار 1 و 4: الملف الشخصي (Profile) =====
# ==========================================
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

# ==========================================
# ===== الخيار 3: لوحة التحكم الإحصائية (Dashboard) =====
# ==========================================
@app.get("/api/dashboard/stats/{user_id}")
def dashboard_stats(user_id: int, db: Session = Depends(get_db)):
    # عدد المشاكل الكلي
    total_solutions = db.query(Solution).filter(Solution.user_id == user_id).count()
    
    # آخر 5 مشاكل
    recent = db.query(Solution).filter(Solution.user_id == user_id).order_by(Solution.created_at.desc()).limit(5).all()
    recent_list = [{"problem": s.problem, "created_at": s.created_at.strftime("%Y-%m-%d %H:%M")} for s in recent]
    
    return {
        "total_solutions": total_solutions,
        "recent": recent_list
    }

@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard_frontend(user_id: int):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>لوحة التحكم - HumanOS</title>
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
            <div id="stats-container">
                <p>⏳ جاري التحميل...</p>
            </div>
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
# ===== الخيار 2: تقرير PDF (طباعة) =====
# ==========================================
@app.get("/report/{solution_id}", response_class=HTMLResponse)
def report_frontend(solution_id: int, db: Session = Depends(get_db)):
    sol = db.query(Solution).filter(Solution.id == solution_id).first()
    if not sol:
        return "<h1>التقرير غير موجود</h1>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>تقرير HumanOS</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; direction: rtl; background: white; padding: 20px; }}
            h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
            .section {{ background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            .label {{ font-weight: bold; color: #555; }}
            button {{ background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
            @media print {{
                .no-print {{ display: none; }}
                body {{ margin: 0; padding: 10px; }}
            }}
        </style>
    </head>
    <body>
        <h1>🧠 تقرير HumanOS</h1>
        <p><strong>📅 التاريخ:</strong> {sol.created_at.strftime("%Y-%m-%d %H:%M")}</p>
        <div class="section">
            <div class="label">❓ المشكلة:</div>
            <p>{sol.problem}</p>
        </div>
        <div class="section">
            <div class="label">📋 التشخيص:</div>
            <p>{sol.diagnosis or "لا يوجد"}</p>
        </div>
        <div class="section">
            <div class="label">🔍 الفجوات:</div>
            <p>{sol.gaps or "لا يوجد"}</p>
        </div>
        <div class="section">
            <div class="label">💡 الحلول المقترحة:</div>
            <p>{sol.solutions or "لا يوجد"}</p>
        </div>
        <div class="section">
            <div class="label">🗓️ الخطة التنفيذية:</div>
            <p>{sol.action_plan or "لا يوجد"}</p>
        </div>
        <button class="no-print" onclick="window.print()">🖨️ طباعة / حفظ كـ PDF</button>
        <br><br>
        <a href="/app" class="no-print">⬅️ الرجوع للرئيسية</a>
    </body>
    </html>
    """

# ==========================================
# ===== الواجهة الرئيسية المطورة (كل الخيارات) =====
# ==========================================
@app.get("/app", response_class=HTMLResponse)
def frontend():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HumanOS</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 30px auto; direction: rtl; background: #f5f5f5; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            input, textarea { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
            button { background: #4CAF50; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #45a049; }
            .btn-blue { background: #2196F3; }
            .btn-blue:hover { background: #1976D2; }
            .btn-purple { background: #9C27B0; }
            .btn-purple:hover { background: #7B1FA2; }
            .btn-orange { background: #FF9800; }
            .btn-orange:hover { background: #F57C00; }
            .result { margin-top: 20px; padding: 15px; border-radius: 8px; display: none; }
            .error { background: #ffebee; color: #c62828; }
            .success { background: #e8f5e9; color: #2e7d32; }
            h1 { color: #333; }
            .label { font-weight: bold; color: #555; margin-top: 10px; }
            .tab { display: inline-block; padding: 10px 20px; cursor: pointer; background: #ddd; border-radius: 8px 8px 0 0; }
            .tab.active { background: #4CAF50; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
            .user-info { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
            .nav-btn { background: #607D8B; color: white; padding: 8px 15px; border-radius: 8px; text-decoration: none; margin: 0 5px; display: inline-block; }
            .nav-btn:hover { background: #455A64; }
            .scenario-box { background: #f3e5f5; padding: 15px; border-radius: 8px; margin: 10px 0; border-right: 4px solid #9C27B0; }
            .profile-field { background: #f5f5f5; padding: 10px; border-radius: 8px; margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🧠 HumanOS</h1>
            <div id="auth-section">
                <div style="margin-bottom:15px;">
                    <span class="tab active" onclick="switchTab('login')" id="login-tab">🔐 دخول</span>
                    <span class="tab" onclick="switchTab('register')" id="register-tab">📝 تسجيل</span>
                </div>
                <div id="register-form" class="tab-content">
                    <h3>إنشاء حساب جديد</h3>
                    <input type="text" id="reg-name" placeholder="الاسم الكامل">
                    <input type="email" id="reg-email" placeholder="البريد الإلكتروني">
                    <input type="password" id="reg-password" placeholder="كلمة السر">
                    <button class="btn-blue" onclick="registerUser()">تسجيل</button>
                    <div id="reg-message"></div>
                </div>
                <div id="login-form" class="tab-content active">
                    <h3>دخول إلى حسابك</h3>
                    <input type="email" id="login-email" placeholder="البريد الإلكتروني">
                    <input type="password" id="login-password" placeholder="كلمة السر">
                    <button class="btn-blue" onclick="loginUser()">دخول</button>
                    <div id="login-message"></div>
                </div>
            </div>

            <div id="solve-section" style="display:none;">
                <div class="user-info" id="user-info-display"></div>
                <div style="margin-bottom:10px;">
                    <a href="#" class="nav-btn" onclick="viewProfile()">👤 ملفي الشخصي</a>
                    <a href="#" class="nav-btn" onclick="viewDashboard()">📊 لوحة التحكم</a>
                    <a href="#" class="nav-btn" onclick="logout()">🚪 خروج</a>
                </div>
                <hr>
                <label for="problem">✍️ مشكلتك:</label>
                <textarea id="problem" rows="4" placeholder="مثلاً: أنا عاطل وعندي خبرة في بايثون"></textarea>
                <button onclick="solveProblem()">🚀 حل المشكلة</button>
                <br>
                <a href="#" class="nav-btn" style="background:#2196F3;" onclick="viewHistory()">📜 تاريخي</a>
                
                <hr>
                <button class="btn-purple" onclick="toggleSimulator()">🔮 محاكي المستقبل</button>
                <div id="simulator-section" style="display:none; margin-top:20px; padding:15px; background:#f3e5f5; border-radius:8px;">
                    <h3>🔮 محاكي المستقبل</h3>
                    <input type="number" id="sim-age" placeholder="العمر" value="30">
                    <input type="text" id="sim-job" placeholder="الوظيفة الحالية" value="مبرمج بايثون">
                    <input type="number" id="sim-income" placeholder="الدخل الشهري" value="1000">
                    <input type="text" id="sim-skills" placeholder="المهارات" value="Python, Django">
                    <input type="text" id="sim-goal" placeholder="الهدف" value="تحسين الوضع المهني">
                    <button class="btn-purple" onclick="simulateFuture()">🚀 احسب سيناريوهاتي</button>
                    <div id="sim-result" style="margin-top:15px;"></div>
                </div>

                <div id="result" class="result"></div>
            </div>
        </div>

        <script>
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

            async function registerUser() {
                const name = document.getElementById('reg-name').value;
                const email = document.getElementById('reg-email').value;
                const password = document.getElementById('reg-password').value;
                const msg = document.getElementById('reg-message');
                if (!name || !email || !password) {
                    msg.innerHTML = '<div class="error">⚠️ جميع الحقول مطلوبة</div>';
                    return;
                }
                try {
                    const res = await fetch('/api/v1/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ full_name: name, email: email, password: password })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        msg.innerHTML = '<div class="success">✅ تم التسجيل! يمكنك الآن الدخول.</div>';
                        switchTab('login');
                    } else {
                        msg.innerHTML = `<div class="error">❌ ${data.detail || 'خطأ'}</div>`;
                    }
                } catch (e) {
                    msg.innerHTML = `<div class="error">❌ خطأ في الاتصال: ${e.message}</div>`;
                }
            }

            async function loginUser() {
                const email = document.getElementById('login-email').value;
                const password = document.getElementById('login-password').value;
                const msg = document.getElementById('login-message');
                if (!email || !password) {
                    msg.innerHTML = '<div class="error">⚠️ جميع الحقول مطلوبة</div>';
                    return;
                }
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
                        msg.innerHTML = '<div class="success">✅ تم الدخول بنجاح!</div>';
                    } else {
                        msg.innerHTML = `<div class="error">❌ ${data.detail || 'خطأ في البريد أو كلمة السر'}</div>`;
                    }
                } catch (e) {
                    msg.innerHTML = `<div class="error">❌ خطأ في الاتصال: ${e.message}</div>`;
                }
            }

            function showSolveSection(email) {
                document.getElementById('auth-section').style.display = 'none';
                document.getElementById('solve-section').style.display = 'block';
                // نجلب الاسم من البروفايل
                fetch(`/profile/${localStorage.getItem('user_id')}`)
                    .then(res => res.json())
                    .then(data => {
                        const name = data.full_name || email;
                        document.getElementById('user-info-display').innerHTML = `👤 مرحباً، ${name} (${email})`;
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
                if (!problem) {
                    resultDiv.innerHTML = '<div class="error">⚠️ من فضلك اكتب مشكلتك أولاً</div>';
                    resultDiv.style.display = 'block';
                    return;
                }
                resultDiv.innerHTML = '🧠 جاري التفكير...';
                resultDiv.style.display = 'block';
                resultDiv.className = 'result';

                try {
                    const response = await fetch('/solve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: parseInt(user_id), problem: problem, language: 'ar' })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let html = '<div class="label">📋 التشخيص</div><p>' + (data.diagnosis || 'لا يوجد') + '</p>';
                        html += '<div class="label">🔍 الفجوات</div><p>' + (data.gaps || 'لا يوجد') + '</p>';
                        html += '<div class="label">💡 الحلول المقترحة</div>';
                        if (data.solutions && data.solutions.length) {
                            html += '<ul>';
                            data.solutions.forEach(s => html += '<li>' + s + '</li>');
                            html += '</ul>';
                        } else { html += '<p>لا يوجد</p>'; }
                        html += '<div class="label">🗓️ الخطة التنفيذية</div><p>' + (data.action_plan || 'لا يوجد') + '</p>';
                        html += `<div style="margin-top:10px;"><a href="/report/${data.solution_id}" target="_blank" class="nav-btn" style="background:#FF9800;">📄 تحميل التقرير (PDF)</a></div>`;
                        resultDiv.innerHTML = html;
                        resultDiv.style.background = '#e8f5e9';
                    } else {
                        resultDiv.innerHTML = '<div class="error">❌ خطأ: ' + (data.error || 'غير معروف') + '</div>';
                        resultDiv.style.background = '#ffebee';
                    }
                } catch (e) {
                    resultDiv.innerHTML = '<div class="error">❌ تعذر الاتصال بالخادم.</div>';
                    resultDiv.style.background = '#ffebee';
                }
            }

            function viewHistory() {
                const user_id = localStorage.getItem('user_id');
                if (user_id) window.location.href = `/history-view/${user_id}`;
                else alert('الرجاء تسجيل الدخول أولاً');
            }

            function viewProfile() {
                const user_id = localStorage.getItem('user_id');
                if (user_id) window.location.href = `/profile-view/${user_id}`;
                else alert('الرجاء تسجيل الدخول أولاً');
            }

            function viewDashboard() {
                const user_id = localStorage.getItem('user_id');
                if (user_id) window.location.href = `/dashboard/${user_id}`;
                else alert('الرجاء تسجيل الدخول أولاً');
            }

            function logout() {
                localStorage.clear();
                window.location.reload();
            }

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
                if (!user_id) { alert('الرجاء تسجيل الدخول أولاً'); return; }
                resultDiv.innerHTML = '🧠 جاري حساب السيناريوهات...';
                try {
                    const res = await fetch('/simulate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: parseInt(user_id), age: parseInt(age), job, income: parseFloat(income), skills, goal, language: 'ar' })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        let html = '<h4>📊 السيناريوهات المستقبلية</h4>';
                        if (data.scenario_stay) {
                            html += `<div style="background:#e3f2fd; padding:10px; border-radius:8px; margin:10px 0;">
                                <h5>🔵 ${data.scenario_stay.title}</h5>
                                <p>${data.scenario_stay.description}</p>
                                <p><strong>الدخل بعد 5 سنوات:</strong> ${data.scenario_stay.income_after_5_years}</p>
                                <p><strong>الرضا:</strong> ${data.scenario_stay.satisfaction}</p>
                            </div>`;
                        }
                        if (data.scenario_learn) {
                            html += `<div style="background:#fff3e0; padding:10px; border-radius:8px; margin:10px 0;">
                                <h5>🟠 ${data.scenario_learn.title}</h5>
                                <p>${data.scenario_learn.description}</p>
                                <p><strong>المهارة المقترحة:</strong> ${data.scenario_learn.skill_to_learn}</p>
                                <p><strong>الدخل بعد 5 سنوات:</strong> ${data.scenario_learn.income_after_5_years}</p>
                                <p><strong>الرضا:</strong> ${data.scenario_learn.satisfaction}</p>
                            </div>`;
                        }
                        if (data.scenario_change) {
                            html += `<div style="background:#e8f5e9; padding:10px; border-radius:8px; margin:10px 0;">
                                <h5>🟢 ${data.scenario_change.title}</h5>
                                <p>${data.scenario_change.description}</p>
                                <p><strong>المهنة الجديدة:</strong> ${data.scenario_change.new_career}</p>
                                <p><strong>الدخل بعد 5 سنوات:</strong> ${data.scenario_change.income_after_5_years}</p>
                                <p><strong>الرضا:</strong> ${data.scenario_change.satisfaction}</p>
                            </div>`;
                        }
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = `<div class="error">❌ خطأ: ${data.error || 'غير معروف'}</div>`;
                    }
                } catch (e) {
                    resultDiv.innerHTML = `<div class="error">❌ خطأ في الاتصال: ${e.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """

# ==========================================
# ===== صفحة عرض التاريخ (HTML) =====
@app.get("/history-view/{user_id}", response_class=HTMLResponse)
def history_frontend(user_id: int):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>تاريخي - HumanOS</title>
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
            <div id="history-container">
                <p>⏳ جاري التحميل...</p>
            </div>
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
    <head>
        <title>ملفي الشخصي - HumanOS</title>
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
            // تحميل البيانات الحالية
            fetch('/profile/{user_id}')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('p-name').value = data.full_name || '';
                    document.getElementById('p-age').value = data.age || '';
                    document.getElementById('p-job').value = data.job_title || '';
                    document.getElementById('p-income').value = data.monthly_income || '';
                    document.getElementById('p-skills').value = data.skills || '';
                }})
                .catch(err => console.log(err));

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
                        msg.innerHTML = '<div class="success">✅ تم حفظ الملف الشخصي بنجاح!</div>';
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