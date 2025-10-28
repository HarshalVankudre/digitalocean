from fastapi import APIRouter
from ..deps import db_dep, admin_dep

router = APIRouter(prefix="/users", tags=["users"]) 

@router.get("/", dependencies=[admin_dep])
async def list_users(db = db_dep):
    cursor = db.users.find({}, {"password_hash": 0})
    return [{"id": str(u["_id"]), **{k:v for k,v in u.items() if k != "_id"}} async for u in cursor]
