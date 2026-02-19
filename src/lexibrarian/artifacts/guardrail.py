"""Pydantic 2 model for guardrail thread artifacts."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

GuardrailStatus = Literal["active", "resolved", "stale"]


class GuardrailThread(BaseModel):
    """Represents a guardrail thread tracking a known footgun or hazard."""

    thread_id: str
    title: str
    status: GuardrailStatus
    scope: list[str]
    reported_by: str
    date: date
    problem: str
    failed_approaches: list[str] = []
    resolution: str | None = None
    evidence: list[str] = []
