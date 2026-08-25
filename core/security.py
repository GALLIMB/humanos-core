import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
import jwt

SECRET_KEY = "my-super-secret-key-123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ===== دوال التشفير باستخدام PBKDF2 (آمن، لا حد 72 حرف) =====
def get_password_hash(password: str) -> str:
    """تشفير كلمة السر باستخدام PBKDF2 مع ملح عشوائي"""
    salt = secrets.token_hex(16)
    # 100000 تكرار (قوي وآمن)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    # نخزن الملح مع التشفير
    return f"pbkdf2_sha256$100000${salt}${hashed.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة السر مقابل التشفير المخزن"""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4:
            return False
        method, iterations, salt, hash_hex = parts
        if method != "pbkdf2_sha256":
            return False
        new_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), int(iterations))
        return hmac.compare_digest(new_hash.hex(), hash_hex)
    except Exception:
        return False

# ===== دوال JWT =====
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt