from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


def _digits_cpf(v: str) -> str:
    d = "".join(c for c in (v or "") if c.isdigit())
    if len(d) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")
    return d


class DataRemovalCheckRequest(BaseModel):
    email: EmailStr
    cpf: str

    @field_validator("cpf", mode="before")
    @classmethod
    def normalize_cpf(cls, v: str) -> str:
        return _digits_cpf(v)


class DataRemovalCheckResponse(BaseModel):
    exists: bool
    message: Optional[str] = None
    reason: Optional[str] = None


class DataRemovalSubmitRequest(BaseModel):
    email: EmailStr
    cpf: str
    confirmed: bool

    @field_validator("cpf", mode="before")
    @classmethod
    def normalize_cpf(cls, v: str) -> str:
        return _digits_cpf(v)


class DataRemovalRequestItem(BaseModel):
    id: int
    email_submitted: str
    cpf_masked: str
    user_id: Optional[int]
    user_name_snapshot: Optional[str]
    match_found: bool
    created_at: Optional[str]
    processed_at: Optional[str]
    request_ip: Optional[str]
