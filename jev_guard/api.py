"""REST API. Request bodies are never logged."""

from __future__ import annotations

import hmac
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from jev_guard.config import Settings
from jev_guard.detectors import ClassifierError
from jev_guard.guard import Guard
from jev_guard.models import ScanResult

_bearer = HTTPBearer(auto_error=False)


class ScanRequest(BaseModel):
    text: str = Field(min_length=1)
    categories: list[str] = Field(default_factory=lambda: ["pii"])
    redact: bool = False


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.guard = Guard.from_settings(settings)
        yield
        app.state.guard.close()

    app = FastAPI(title="jev-guard", lifespan=lifespan, docs_url=None, redoc_url=None)

    def authorize(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
        if settings.api_key is None:
            return
        supplied = creds.credentials if creds else ""
        if not hmac.compare_digest(supplied.encode(), settings.api_key.encode()):
            raise HTTPException(status_code=401, detail="Unauthorized")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/scan", response_model=ScanResult, dependencies=[Depends(authorize)])
    def scan(body: ScanRequest, request: Request) -> ScanResult:
        if len(body.text) > settings.max_chars:
            raise HTTPException(status_code=413, detail="Text too large")
        try:
            return request.app.state.guard.scan(
                body.text, tuple(body.categories), redact_text=body.redact
            )
        except ValueError as exc:  # unsupported category
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except ClassifierError:
            # Fail closed: never report "clean" when the classifier was unavailable.
            raise HTTPException(status_code=502, detail="Classifier unavailable") from None

    return app
