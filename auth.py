from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "این-رو-بعدا-عوض-میکنیم-فعلا-تست"
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60 * 24  # one day

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None