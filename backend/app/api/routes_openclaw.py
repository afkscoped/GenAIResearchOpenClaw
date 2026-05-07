from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, HTTPException

from app.agent.openclaw_client import analyze
from app.core.config import get_settings
from app.schemas.openclaw import OpenClawAnalyzeRequest, OpenClawAnalyzeResponse, OpenClawCredentials, OpenClawStatus

router = APIRouter(prefix="/api/openclaw", tags=["openclaw"])
_credentials_cache: OpenClawCredentials | None = None


@router.post("/analyze", response_model=OpenClawAnalyzeResponse)
def analyze_with_openclaw(payload: OpenClawAnalyzeRequest) -> OpenClawAnalyzeResponse:
    result = analyze(title=payload.title, abstract=payload.abstract, scores=payload.scores)
    return OpenClawAnalyzeResponse(
        prism_score=result.prism_score,
        verdict=result.verdict,
        reasoning=result.reasoning,
        action=result.action,
        source=result.source,
    )


@router.get("/status", response_model=OpenClawStatus)
def openclaw_status() -> OpenClawStatus:
    settings = get_settings()
    credentials = _load_credentials()
    return OpenClawStatus(
        enable_openclaw=settings.enable_openclaw,
        openclaw_url=settings.openclaw_url,
        has_discord_webhook=bool(settings.discord_webhook_url),
        has_llm_key=bool(settings.llm_api_key),
        credentials_configured={
            "discord_bot": bool(credentials.discord_bot_token),
            "discord_webhook": bool(credentials.discord_webhook_url or settings.discord_webhook_url),
            "telegram": bool(credentials.telegram_bot_token and credentials.telegram_chat_id),
            "reddit": bool(credentials.reddit_client_id and credentials.reddit_client_secret),
        },
    )


@router.post("/credentials", response_model=OpenClawStatus)
def set_openclaw_credentials(payload: OpenClawCredentials) -> OpenClawStatus:
    global _credentials_cache
    _credentials_cache = payload
    _save_credentials(payload)
    return openclaw_status()


def _credentials_path() -> Path:
    path = Path(get_settings().openclaw_credentials_path)
    return path if path.is_absolute() else Path.cwd() / path


def _key_path() -> Path:
    path = Path(get_settings().openclaw_credentials_key_path)
    return path if path.is_absolute() else Path.cwd() / path


def _fernet() -> Fernet:
    key_path = _key_path()
    if key_path.exists():
        key = key_path.read_bytes()
    else:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        key_path.write_bytes(key)
    return Fernet(key)


def _load_credentials() -> OpenClawCredentials:
    global _credentials_cache
    if _credentials_cache is not None:
        return _credentials_cache
    path = _credentials_path()
    if not path.exists():
        _credentials_cache = OpenClawCredentials()
        return _credentials_cache
    try:
        data = _fernet().decrypt(path.read_bytes())
        _credentials_cache = OpenClawCredentials.model_validate_json(data)
        return _credentials_cache
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(status_code=500, detail="OpenClaw credentials could not be decrypted") from exc


def _save_credentials(credentials: OpenClawCredentials) -> None:
    path = _credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_fernet().encrypt(credentials.model_dump_json().encode("utf-8")))
