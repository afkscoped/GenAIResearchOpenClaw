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
    groq_api_key_present: bool = False
    ollama_model: str | None = None


class OpenClawStatus(BaseModel):
    enable_openclaw: bool
    openclaw_url: str
    has_llm_key: bool
    ollama_base_url: str
    ollama_model: str
    credentials_configured: dict[str, bool]
