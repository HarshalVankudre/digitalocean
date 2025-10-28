from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..schemas import UserCreate, UserPublic, TokenResponse
from ..auth import hash_password, verify_password, create_access_token
from ..deps import db_dep, admin_dep

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic)
async def register(user_in: UserCreate, db = db_dep):
    if await db.users.find_one({"email": user_in.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = {
        "email": user_in.email,
        "password_hash": hash_password(user_in.password),
        "name": user_in.name,
        "role": user_in.role,
        "created_at": datetime.utcnow(),
    }
    res = await db.users.insert_one(doc)
    return UserPublic(id=str(res.inserted_id), email=doc["email"], name=doc["name"], role=doc["role"], created_at=doc["created_at"])

@router.post("/login", response_model=TokenResponse)
async def login(email: str, password: str, db = db_dep):
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return TokenResponse(access_token=token)
