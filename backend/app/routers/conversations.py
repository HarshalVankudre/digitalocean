from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from ..deps import db_dep, user_dep
from ..schemas import ConversationCreate, ConversationPublic, ConversationDetail, MessageCreate, MessagePublic
from ..services.do_agent import call_do_agent
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from bson import ObjectId
import httpx
import json
import anyio
from ..deps import db_dep, user_dep
from ..schemas import MessageCreate

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


@router.post("/{cid}/stream")
async def send_streaming_message(cid: str, msg: MessageCreate, db = db_dep, user = user_dep):
    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Persist the user message first
    user_doc = {
        "conversation_id": conv["_id"],
        "role": "user",
        "content": msg.content,
        "created_at": datetime.utcnow(),
    }
    await db.messages.insert_one(user_doc)

    # Read app settings (agent endpoint & key)
    settings = await db.app_settings.find_one({"_id": "singleton"}) or {}
    base_url = (settings.get("do_agent_base_url") or "").rstrip("/")
    access_key = settings.get("do_agent_access_key") or ""
    if not base_url or not access_key:
        raise HTTPException(status_code=400, detail="Agent settings missing")

    # Prepare DigitalOcean Agent payload
    payload = {
        "messages": [
            {"role": "user", "content": msg.content}
        ],
        "stream": True,
        "include_retrieval_info": bool(settings.get("include_retrieval_info", False)),
        "include_functions_info": bool(settings.get("include_functions_info", False)),
        "include_guardrails_info": bool(settings.get("include_guardrails_info", False)),
    }

    async def do_stream():
        # Keep an accumulator to save the final assistant message
        assistant_accum = []
        async with httpx.AsyncClient(timeout=None) as client:
            url = f"{base_url}/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {access_key}",
                "Content-Type": "application/json",
            }
            async with client.stream("POST", url, headers=headers, json=payload) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    if not chunk:
                        continue
                    text = chunk.decode("utf-8", errors="ignore")
                    # Forward as Server-Sent Events style (works with fetch reader above)
                    # If provider already returns SSE lines, we just forward them line-by-line.
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        # Try to extract plain text deltas if response is JSON chunks
                        # Fallback: forward raw
                        try:
                            obj = json.loads(line)
                            # Adapt to your agent’s stream shape; here we try OpenAI-like chunks:
                            delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                            if delta:
                                assistant_accum.append(delta)
                                yield f"data: {delta}\n\n"
                            # If agent sends a "[DONE]" marker:
                            if obj.get("done"):
                                yield "data: [DONE]\n\n"
                        except Exception:
                            assistant_accum.append(line)
                            yield f"data: {line}\n\n"

        # Save the assistant message after the stream ends
        full_text = "".join(assistant_accum).strip()
        if full_text:
            await db.messages.insert_one({
                "conversation_id": conv["_id"],
                "role": "assistant",
                "content": full_text,
                "created_at": datetime.utcnow(),
            })
            await db.conversations.update_one(
                {"_id": conv["_id"]},
                {"$set": {"updated_at": datetime.utcnow(), "title": conv.get("title") or full_text[:60]}}
            )

    # Return a streaming response
    return StreamingResponse(do_stream(), media_type="text/event-stream")