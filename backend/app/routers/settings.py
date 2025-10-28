from fastapi import APIRouter
from ..deps import db_dep, admin_dep
from ..schemas import SettingsPublic, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"]) 

@router.get("/", response_model=SettingsPublic, dependencies=[admin_dep])
async def get_settings(db = db_dep):
    doc = await db.app_settings.find_one({}) or {}
    return SettingsPublic(
        do_agent_base_url=doc.get("do_agent_base_url"),
        do_agent_access_key=doc.get("do_agent_access_key"),
        include_retrieval_info=doc.get("include_retrieval_info", True),
        include_functions_info=doc.get("include_functions_info", False),
        include_guardrails_info=doc.get("include_guardrails_info", False),
    )

@router.put("/", response_model=SettingsPublic, dependencies=[admin_dep])
async def update_settings(payload: SettingsUpdate, db = db_dep):
    doc = await db.app_settings.find_one({}) or {}
    update = {k:v for k,v in payload.model_dump(exclude_unset=True).items()}
    doc.update(update)
    await db.app_settings.replace_one({"_id": doc.get("_id", None) or "singleton"}, {**doc, "_id": "singleton"}, upsert=True)
    return await get_settings(db)
