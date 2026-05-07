from pydantic import BaseModel, Field


class OpenClawAnalyzeRequest(BaseModel):
    title: str
    abstract: str = ""
    scores: dict[str, float] = Field(default_factory=dict)


class OpenClawAnalyzeResponse(BaseModel):
    prism_score: float
    verdict: str
    reasoning: str
    action: str
    source: str


class OpenClawCredentials(BaseModel):
    discord_bot_token: str | None = None
    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_username: str | None = None
    reddit_password: str | None = None


class OpenClawStatus(BaseModel):
    enable_openclaw: bool
    openclaw_url: str
    has_discord_webhook: bool
    has_llm_key: bool
    credentials_configured: dict[str, bool]
