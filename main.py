from fastapi import FastAPI
from pydantic import BaseModel
from ai_gateway import solve_problem

app = FastAPI(title="HumanOS Core", version="0.0.1")

@app.get("/")
def read_root():
    return {"message": "مرحبا بك في HumanOS!"}

@app.get("/health")
def health_check():
    return {"status": "alive"}

class ProblemRequest(BaseModel):
    problem: str
    language: str = "ar"

@app.post("/solve")
def solve(problem_req: ProblemRequest):
    result = solve_problem(problem_req.problem, problem_req.language)
    return result