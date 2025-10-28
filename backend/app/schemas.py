from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal, Any
from datetime import datetime

Role = Literal["admin", "user"]

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Role = "user"

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: Role
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SettingsPublic(BaseModel):
    do_agent_base_url: Optional[str] = None
    do_agent_access_key: Optional[str] = None
    include_retrieval_info: bool = True
    include_functions_info: bool = False
    include_guardrails_info: bool = False

class SettingsUpdate(BaseModel):
    do_agent_base_url: Optional[str] = None
    do_agent_access_key: Optional[str] = None
    include_retrieval_info: Optional[bool] = None
    include_functions_info: Optional[bool] = None
    include_guardrails_info: Optional[bool] = None

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    stream: bool = False

class MessagePublic(BaseModel):
    id: str
    role: Literal["user","assistant"]
    content: str
    retrieval: Optional[Any] = None
    guardrails: Optional[Any] = None
    functions: Optional[Any] = None
    created_at: datetime

class ConversationPublic(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

class ConversationDetail(ConversationPublic):
    messages: List[MessagePublic] = []
