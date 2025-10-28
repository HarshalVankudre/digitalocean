from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from ..deps import db_dep, user_dep
from ..schemas import ConversationCreate, ConversationPublic, ConversationDetail, MessageCreate, MessagePublic
from ..services.do_agent import call_do_agent

router = APIRouter(prefix="/conversations", tags=["conversations"]) 

@router.post("/", response_model=ConversationPublic)
async def create_conversation(body: ConversationCreate, db = db_dep, user = user_dep):
    now = datetime.utcnow()
    doc = {
        "user_id": ObjectId(user["id"]),
        "title": body.title or "New chat",
        "created_at": now,
        "updated_at": now,
    }
    res = await db.conversations.insert_one(doc)
    return {"id": str(res.inserted_id), "title": doc["title"], "created_at": now, "updated_at": now}

@router.get("/", response_model=list[ConversationPublic])
async def list_conversations(db = db_dep, user = user_dep):
    cursor = db.conversations.find({"user_id": ObjectId(user["id"])})
    items = []
    async for c in cursor:
        items.append({"id": str(c["_id"]), "title": c.get("title"), "created_at": c["created_at"], "updated_at": c["updated_at"]})
    return items

@router.get("/{cid}", response_model=ConversationDetail)
async def get_conversation(cid: str, db = db_dep, user = user_dep):
    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = []
    async for m in db.messages.find({"conversation_id": conv["_id"]}).sort("created_at", 1):
        msgs.append(MessagePublic(
            id=str(m["_id"]), role=m["role"], content=m["content"],
            retrieval=m.get("retrieval"), guardrails=m.get("guardrails"), functions=m.get("functions"),
            created_at=m["created_at"],
        ).model_dump())
    return {
        "id": str(conv["_id"]),
        "title": conv.get("title"),
        "created_at": conv["created_at"],
        "updated_at": conv["updated_at"],
        "messages": msgs,
    }

@router.post("/{cid}/messages", response_model=MessagePublic)
async def send_message(cid: str, body: MessageCreate, db = db_dep, user = user_dep):
    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # save user message first
    now = datetime.utcnow()
    user_msg = {"conversation_id": conv["_id"], "role": "user", "content": body.content, "created_at": now}
    await db.messages.insert_one(user_msg)

    # load app settings (fallback to env)
    s = await db.app_settings.find_one({}) or {}
    base_url = s.get("do_agent_base_url")
    access_key = s.get("do_agent_access_key")
    if not base_url or not access_key:
        raise HTTPException(status_code=400, detail="Agent endpoint not configured by admin")

    include_retrieval_info = s.get("include_retrieval_info", True)
    include_functions_info = s.get("include_functions_info", False)
    include_guardrails_info = s.get("include_guardrails_info", False)

    # Gather full history for this conversation
    history = []
    async for m in db.messages.find({"conversation_id": conv["_id"]}).sort("created_at", 1):
        history.append({"role": m["role"], "content": m["content"]})

    resp_json = await call_do_agent(
        base_url=base_url,
        access_key=access_key,
        messages=history,
        include_retrieval_info=include_retrieval_info,
        include_functions_info=include_functions_info,
        include_guardrails_info=include_guardrails_info,
        stream=False,
    )

    # parse assistant reply
    content = (resp_json.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
    retrieval = resp_json.get("retrieval")
    guardrails = resp_json.get("guardrails")
    functions = resp_json.get("functions")

    asst_doc = {
        "conversation_id": conv["_id"],
        "role": "assistant",
        "content": content,
        "retrieval": retrieval,
        "guardrails": guardrails,
        "functions": functions,
        "created_at": datetime.utcnow(),
    }
    ins = await db.messages.insert_one(asst_doc)

    # bump conversation timestamp
    await db.conversations.update_one({"_id": conv["_id"]}, {"$set": {"updated_at": datetime.utcnow()}})

    return MessagePublic(
        id=str(ins.inserted_id), role="assistant", content=content,
        retrieval=retrieval, guardrails=guardrails, functions=functions,
        created_at=asst_doc["created_at"],
    )

@router.patch("/{cid}", response_model=ConversationPublic)
async def rename_conversation(cid: str, payload: dict, db = db_dep, user = user_dep):
    """
    Payload: { "title": "New Title" }
    """
    if "title" not in payload or not str(payload["title"]).strip():
        raise HTTPException(status_code=400, detail="title is required")

    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    new_title = str(payload["title"]).strip()
    await db.conversations.update_one(
        {"_id": conv["_id"]},
        {"$set": {"title": new_title, "updated_at": datetime.utcnow()}}
    )
    conv["title"] = new_title
    return {
        "id": str(conv["_id"]),
        "title": conv["title"],
        "created_at": conv["created_at"],
        "updated_at": datetime.utcnow(),
    }

@router.delete("/{cid}")
async def delete_conversation(cid: str, db = db_dep, user = user_dep):
    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # delete messages then the conversation
    await db.messages.delete_many({ "conversation_id": conv["_id"] })
    await db.conversations.delete_one({ "_id": conv["_id"] })
    return {"ok": True}