from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "user"


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    role: str


class ChatIssue(BaseModel):
    title: str = ""
    body: str = ""


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    issue: ChatIssue | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    tool_calls: list[dict]
    trace_id: str


class MemoryCreate(BaseModel):
    text: str
    metadata: dict = {}


class WidgetConfigIn(BaseModel):
    widget_id: str
    allowed_origins: list[str] = ["*"]
    theme: dict = {}
    greeting: str = "Hi! How can I help?"
    enabled_tools: list[str] = ["rag_search"]


class WidgetConfigPatch(BaseModel):
    allowed_origins: list[str] | None = None
    theme: dict | None = None
    greeting: str | None = None
    enabled_tools: list[str] | None = None
