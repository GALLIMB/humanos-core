from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ...db.session import get_db
from ...models.user import User
from ...core.security import get_password_hash, verify_password, create_access_token
import traceback

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # 1. نتأكد أن الإيميل مش مسجل
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 2. تشفير كلمة السر
        hashed = get_password_hash(user.password)
        
        # 3. إنشاء المستخدم
        new_user = User(email=user.email, hashed_password=hashed, full_name=user.full_name)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"message": "User created successfully", "user_id": new_user.id}
    
    except Exception as e:
        # هادي أهم نقطة: نطبع الخطأ الحقيقي في نافذة PowerShell
        print("="*50)
        print("🔥 خطأ في التسجيل:")
        traceback.print_exc()
        print("="*50)
        # نرجع الخطأ للمستخدم
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token(data={"sub": db_user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "email": db_user.email
        }
    except Exception as e:
        print("="*50)
        print("🔥 خطأ في الدخول:")
        traceback.print_exc()
        print("="*50)
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")