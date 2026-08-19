from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ai_gateway import solve_problem
from humanos.db.session import get_db, engine, Base
from humanos.models import user
from humanos.models.solution import Solution
import json

# ننشئ الجداول في قاعدة البيانات
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HumanOS Core", version="0.0.1")

# ===== المسارات الأساسية =====
@app.get("/")
def read_root():
    return {"message": "مرحبا بك في HumanOS!"}

@app.get("/health")
def health_check():
    return {"status": "alive", "db": "sqlite"}

# ===== نموذج البيانات القادم من المستخدم =====
class ProblemRequest(BaseModel):
    user_id: int
    problem: str
    language: str = "ar"

# ===== مسار حل المشكلات (يحفظ في القاعدة) =====
@app.post("/solve")
def solve(problem_req: ProblemRequest, db: Session = Depends(get_db)):
    # 1. نشغل الذكاء الاصطناعي باش يحلل
    ai_result = solve_problem(problem_req.problem, problem_req.language)
    
    # 2. نستخرج البيانات من الـ JSON لي رجعه الذكاء
    diagnosis = ai_result.get("diagnosis")
    gaps = ai_result.get("gaps")
    solutions_list = ai_result.get("solutions")
    action_plan = ai_result.get("action_plan")
    
    # نحول قائمة الحلول إلى نص JSON باش نخزنها في القاعدة
    solutions_json = json.dumps(solutions_list) if solutions_list else None

    # 3. نخزن كل شيء في قاعدة البيانات
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

    # 4. نرجع للمستخدم النتيجة مع رقم الحفظ
    return {
        "solution_id": new_solution.id,
        "diagnosis": diagnosis,
        "gaps": gaps,
        "solutions": solutions_list,
        "action_plan": action_plan
    }

# ===== جلب تاريخ التحليلات (API) =====
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

# ===== واجهة المستخدم الرئيسية (HTML) =====
@app.get("/app", response_class=HTMLResponse)
def frontend():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>HumanOS</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; direction: rtl; background: #f5f5f5; }
            .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
            button { background: #4CAF50; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #45a049; }
            .result { margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px; display: none; }
            .error { background: #ffebee; color: #c62828; }
            h1 { color: #333; }
            .label { font-weight: bold; color: #555; margin-top: 10px; }
            .history-btn { display: inline-block; margin-top: 10px; padding: 10px 20px; background: #2196F3; color: white; text-decoration: none; border-radius: 8px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🧠 HumanOS</h1>
            <p>أخبرني مشكلتك وسأساعدك في حلها</p>
            
            <label for="user_id">🆔 رقم المستخدم (ضع 1 إذا ما سجلتش)</label>
            <input type="number" id="user_id" value="1" style="width:100%; padding:8px; margin:10px 0; border:1px solid #ddd; border-radius:8px;">
            
            <label for="problem">✍️ مشكلتك:</label>
            <textarea id="problem" rows="4" placeholder="مثلاً: أنا عاطل وعندي خبرة في بايثون"></textarea>
            
            <button onclick="solveProblem()">🚀 حل المشكلة</button>
            <br>
            <a href="/history-view/1" class="history-btn">📜 تاريخي</a>
            
            <div id="result" class="result"></div>
        </div>

        <script>
            async function solveProblem() {
                const user_id = document.getElementById('user_id').value;
                const problem = document.getElementById('problem').value;
                const resultDiv = document.getElementById('result');

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
                        } else {
                            html += '<p>لا يوجد</p>';
                        }
                        html += '<div class="label">🗓️ الخطة التنفيذية</div><p>' + (data.action_plan || 'لا يوجد') + '</p>';
                        html += '<div style="margin-top:10px; font-size:12px; color:#888;">🆔 رقم الحفظ: ' + (data.solution_id || 'غير معروف') + '</div>';
                        resultDiv.innerHTML = html;
                        resultDiv.style.background = '#e8f5e9';
                    } else {
                        resultDiv.innerHTML = '<div class="error">❌ خطأ: ' + (data.error || 'غير معروف') + '</div>';
                        resultDiv.style.background = '#ffebee';
                    }
                } catch (e) {
                    resultDiv.innerHTML = '<div class="error">❌ تعذر الاتصال بالخادم. تأكد أنه شغال على port 8000.</div>';
                    resultDiv.style.background = '#ffebee';
                }
            }
        </script>
    </body>
    </html>
    """

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
            <p>المستخدم رقم: {user_id}</p>
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
                                </div>
                            `;
                        }});
                        container.innerHTML = html;
                    }} else {{
                        container.innerHTML = `<div class="empty">📭 مازال ما عندكش تحليلات. اذهب للرئيسية واكتب مشكلتك الأولى!</div>`;
                    }}
                }})
                .catch(err => {{
                    document.getElementById('history-container').innerHTML = `<div class="empty">❌ خطأ في التحميل: ${{err.message}}</div>`;
                }});
        </script>
    </body>
    </html>
    """