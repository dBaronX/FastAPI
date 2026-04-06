from fastapi import Header, HTTPException
import os
from jose import jwt

JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")