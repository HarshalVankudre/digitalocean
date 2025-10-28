from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from bson import ObjectId
import httpx
import json
from ..deps import db_dep, user_dep
from ..schemas import ConversationCreate, ConversationPublic, ConversationDetail, MessageCreate, MessagePublic
from ..services.do_agent import call_do_agent

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationPublic)
async def create_conversation(body: ConversationCreate, db=db_dep, user=user_dep):
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
async def list_conversations(db=db_dep, user=user_dep):
    cursor = db.conversations.find({"user_id": ObjectId(user["id"])})
    items = []
    async for c in cursor:
        items.append({"id": str(c["_id"]), "title": c.get("title"), "created_at": c["created_at"],
                      "updated_at": c["updated_at"]})
    return items


@router.get("/{cid}", response_model=ConversationDetail)
async def get_conversation(cid: str, db=db_dep, user=user_dep):
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


# STREAMING ENDPOINT - This is now the ONLY way to send messages
@router.post("/{cid}/messages/stream")
async def send_streaming_message(cid: str, msg: MessageCreate, db=db_dep, user=user_dep):
    print(f"\n✅ ✅ ✅ [STREAM ENDPOINT CALLED] for conversation {cid} ✅ ✅ ✅\n")

    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_doc = {
        "conversation_id": conv["_id"],
        "role": "user",
        "content": msg.content,
        "created_at": datetime.utcnow(),
    }
    await db.messages.insert_one(user_doc)

    settings = await db.app_settings.find_one({"_id": "singleton"}) or {}
    base_url = (settings.get("do_agent_base_url") or "").rstrip("/")
    access_key = settings.get("do_agent_access_key") or ""
    if not base_url or not access_key:
        raise HTTPException(status_code=400, detail="Agent settings missing")

    history = []
    async for m in db.messages.find({"conversation_id": conv["_id"]}).sort("created_at", 1):
        history.append({"role": m["role"], "content": m["content"]})

    payload = {
        "messages": history,
        "stream": True,
        "include_retrieval_info": bool(settings.get("include_retrieval_info", False)),
        "include_functions_info": bool(settings.get("include_functions_info", False)),
        "include_guardrails_info": bool(settings.get("include_guardrails_info", False)),
    }

    async def do_stream():
        print("--- [do_stream]: Starting stream ---")
        assistant_accum = []
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                url = f"{base_url}/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {access_key}",
                    "Content-Type": "application/json",
                }
                print(f"--- [do_stream]: Making request to {url}")
                async with client.stream("POST", url, headers=headers, json=payload) as r:
                    print(f"--- [do_stream]: Got response status: {r.status_code} ---")

                    r.raise_for_status()

                    print("--- [do_stream]: Status OK, starting line iteration ---")
                    async for line in r.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()

                        if data_str == "[DONE]":
                            print("--- [do_stream]: Received [DONE] signal ---")
                            yield "data: [DONE]\n\n"
                            break
                        if not data_str:
                            continue

                        try:
                            obj = json.loads(data_str)
                            delta_content = None

                            choices = obj.get("choices")
                            if choices and isinstance(choices, list) and len(choices) > 0:
                                delta = choices[0].get("delta")
                                if delta and isinstance(delta, dict):
                                    if "content" in delta:
                                        delta_content = delta.get("content")

                            if delta_content:
                                assistant_accum.append(delta_content)
                                yield f"data: {delta_content}\n\n"

                        except json.JSONDecodeError:
                            print(f"--- [do_stream] WARNING: Failed to decode JSON: {data_str} ---")
                            pass
                        except Exception as e:
                            print(f"--- [do_stream] WARNING: Error parsing stream: {e} ---")
                            pass

                    print("--- [do_stream]: Finished line iteration ---")

        except httpx.HTTPStatusError as e:
            error_text = await e.response.aread()
            print(f"\n!!! HTTPStatusError: {e.response.status_code}")
            print(f"!!! Agent Error: {error_text.decode()}\n")
            raise e
        except Exception as e:
            print(f"\n!!! UNKNOWN ERROR: {e}")
            print(f"!!! Payload: {json.dumps(payload, indent=2)}\n")
            raise e

        full_text = "".join(assistant_accum).strip()
        if full_text:
            print(f"--- [do_stream]: Saving {len(full_text)} chars to DB ---")
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

    return StreamingResponse(do_stream(), media_type="text/event-stream")


# REMOVED - Non-streaming endpoint deleted to force streaming
# If you see a 404 for /messages, that means your frontend is calling the wrong endpoint!

@router.patch("/{cid}", response_model=ConversationPublic)
async def rename_conversation(cid: str, payload: dict, db=db_dep, user=user_dep):
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
async def delete_conversation(cid: str, db=db_dep, user=user_dep):
    conv = await db.conversations.find_one({"_id": ObjectId(cid), "user_id": ObjectId(user["id"])})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.messages.delete_many({"conversation_id": conv["_id"]})
    await db.conversations.delete_one({"_id": conv["_id"]})
    return {"ok": True}