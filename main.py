from fastapi import FastAPI

app = FastAPI(title="HumanOS Core", version="0.0.1")

@app.get("/")
def read_root():
    return {"message": "مرحبا بك في HumanOS!"}

@app.get("/health")
def health_check():
    return {"status": "alive"}