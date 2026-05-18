"""Pydantic schemas for all API models."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
import re


# ────────────── Common ──────────────

class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int


# ────────────── Auth ──────────────

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=32)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含数字")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=32)


# ────────────── User ──────────────

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: str
    balance: int
    status: str
    api_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    status: Optional[str] = None
    balance: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=32)


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_prefix: str
    enabled: bool
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ApiKeyCreatedResponse(BaseModel):
    api_key: ApiKeyOut
    raw_key: str


# ────────────── Asset ──────────────

class AssetBase(BaseModel):
    type: str
    name: str = Field(..., max_length=100)
    enabled: bool = True
    visibility: str = "private"
    notes: Optional[str] = Field(None, max_length=200)
    # LLM
    provider: Optional[str] = None
    protocol: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_names: Optional[List[str]] = None
    max_tokens: Optional[int] = 4096
    timeout_seconds: Optional[int] = 60
    max_retries: Optional[int] = 3
    temperature: Optional[float] = 0.7
    group_ids: Optional[List[str]] = None
    # MCP
    tool_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    method: Optional[str] = None
    authentication_type: Optional[str] = None
    parameter_schema: Optional[dict] = None
    required_parameters: Optional[List[str]] = None
    response_mapping: Optional[dict] = None
    # Memory
    index_name: Optional[str] = None
    max_tokens_capacity: Optional[int] = None
    persist: Optional[bool] = False
    expire_days: Optional[int] = None


class AssetCreateRequest(AssetBase):
    pass


class AssetUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    visibility: Optional[str] = None
    notes: Optional[str] = None
    provider: Optional[str] = None
    protocol: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_names: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    temperature: Optional[float] = None
    group_ids: Optional[List[str]] = None
    tool_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    method: Optional[str] = None
    authentication_type: Optional[str] = None
    parameter_schema: Optional[dict] = None
    required_parameters: Optional[List[str]] = None
    response_mapping: Optional[dict] = None
    index_name: Optional[str] = None
    max_tokens_capacity: Optional[int] = None
    persist: Optional[bool] = None
    expire_days: Optional[int] = None


class AssetOut(BaseModel):
    id: str
    owner_id: str
    type: str
    name: str
    enabled: bool
    connectivity: str
    visibility: str
    notes: Optional[str] = None
    provider: Optional[str] = None
    protocol: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_names: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    temperature: Optional[float] = None
    group_ids: Optional[List[str]] = None
    tool_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    method: Optional[str] = None
    authentication_type: Optional[str] = None
    parameter_schema: Optional[dict] = None
    required_parameters: Optional[List[str]] = None
    response_mapping: Optional[dict] = None
    index_name: Optional[str] = None
    max_tokens_capacity: Optional[int] = None
    persist: Optional[bool] = None
    expire_days: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("api_key")
    @classmethod
    def mask_api_key(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 4:
            return "****" + v[-4:]
        return v

    class Config:
        from_attributes = True


class AssetTestResult(BaseModel):
    success: bool
    latency_ms: int
    message: str
    tested_at: datetime


class AssetToggleRequest(BaseModel):
    enabled: bool


# ────────────── Guardrail ──────────────

class GuardrailCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    guardrail_type: str
    domain: str
    position: str
    description: Optional[str] = Field(None, max_length=200)
    default_priority: int = Field(default=50, ge=1, le=100)
    enabled: bool = True
    endpoint_url: str
    timeout_ms: int = 3000
    retry_count: int = 0
    health_check_path: Optional[str] = None
    supports_multimodal: bool = False
    streaming_enabled: bool = False
    window_tokens: Optional[int] = 100
    window_overlap: Optional[int] = 20
    hit_action: str = "block"
    alert_methods: Optional[List[str]] = None
    alert_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    correct_template: Optional[str] = None
    match_conditions: Optional[dict] = None
    ext_params: Optional[dict] = None


class GuardrailUpdateRequest(BaseModel):
    name: Optional[str] = None
    guardrail_type: Optional[str] = None
    domain: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None
    default_priority: Optional[int] = None
    enabled: Optional[bool] = None
    endpoint_url: Optional[str] = None
    timeout_ms: Optional[int] = None
    retry_count: Optional[int] = None
    health_check_path: Optional[str] = None
    supports_multimodal: Optional[bool] = None
    streaming_enabled: Optional[bool] = None
    window_tokens: Optional[int] = None
    window_overlap: Optional[int] = None
    hit_action: Optional[str] = None
    alert_methods: Optional[List[str]] = None
    alert_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    correct_template: Optional[str] = None
    match_conditions: Optional[dict] = None
    ext_params: Optional[dict] = None


class GuardrailOut(BaseModel):
    id: str
    owner_id: str
    name: str
    guardrail_type: str
    domain: str
    position: str
    description: Optional[str] = None
    default_priority: int
    enabled: bool
    endpoint_url: str
    timeout_ms: int
    retry_count: int
    health_check_path: Optional[str] = None
    supports_multimodal: bool
    streaming_enabled: bool
    window_tokens: Optional[int] = None
    window_overlap: Optional[int] = None
    hit_action: str
    alert_methods: Optional[List[str]] = None
    alert_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    correct_template: Optional[str] = None
    match_conditions: Optional[dict] = None
    ext_params: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GuardrailTestRequest(BaseModel):
    messages: List[dict]
    metadata: dict = {}


class GuardrailTestResult(BaseModel):
    verdict: str
    reason: Optional[str] = None
    confidence: float
    latency_ms: int
    raw_response: dict


# ────────────── Traffic Config ──────────────

class TrafficConfigCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=200)
    enabled: bool = True
    execution_mode: str = "serial"
    asset_ids: List[str] = []
    guardrail_entries: List[dict] = []


class TrafficConfigUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    execution_mode: Optional[str] = None
    asset_ids: Optional[List[str]] = None
    guardrail_entries: Optional[List[dict]] = None


class TrafficConfigOut(BaseModel):
    id: str
    owner_id: str
    name: str
    description: Optional[str] = None
    enabled: bool
    execution_mode: str
    assets_summary: Optional[List[dict]] = None
    pre_guardrail_count: int = 0
    post_guardrail_count: int = 0
    request_count_24h: int = 0
    block_rate_24h: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrafficConfigDetailOut(TrafficConfigOut):
    asset_ids: List[str] = []
    guardrail_entries: List[dict] = []


# ────────────── Request Log ──────────────

class RequestLogOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    request_id: str
    model: str
    status: str
    request_tokens: int
    response_tokens: int
    latency_ms: int
    cost: float
    points_consumed: int
    blocked_by: Optional[str] = None
    block_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RequestLogDetailOut(RequestLogOut):
    request_messages: Optional[Any] = None
    response_content: Optional[str] = None
    guardrail_results: Optional[Any] = None
    traffic_config_id: Optional[str] = None
    asset_id: Optional[str] = None


# ────────────── Dashboard ──────────────

class DashboardStats(BaseModel):
    total_requests_24h: int = 0
    blocked_requests_24h: int = 0
    block_rate_24h: float = 0.0
    avg_latency_ms_24h: float = 0.0
    total_tokens_24h: int = 0
    points_consumed_24h: int = 0
    active_users_24h: int = 0
    chart_data: List[dict] = []


# ────────────── Alert ──────────────

class AlertRuleCreateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    metric: str
    condition: str
    threshold: float
    window_minutes: int = 5
    notify_methods: List[str] = []
    notify_users: List[str] = []
    webhook_url: Optional[str] = None


class AlertRuleOut(BaseModel):
    id: str
    user_id: str
    name: str
    enabled: bool
    metric: str
    condition: str
    threshold: float
    window_minutes: int
    notify_methods: List[str]
    last_triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertEventOut(BaseModel):
    id: str
    rule_id: Optional[str] = None
    level: str
    title: str
    message: Optional[str] = None
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ────────────── Billing ──────────────

class RechargeRequest(BaseModel):
    amount_points: int = Field(..., gt=0)
    amount_money: float = Field(..., gt=0)


class PointsConsumptionOut(BaseModel):
    id: str
    points: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ────────────── Settings ──────────────

class SystemSettingUpdate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


# ────────────── Toggle/Update Schemas ──────────────

class GuardrailToggleRequest(BaseModel):
    enabled: bool


class TrafficConfigToggleRequest(BaseModel):
    enabled: bool


class AlertRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    metric: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    window_minutes: Optional[int] = None
    notify_methods: Optional[List[str]] = None
    notify_users: Optional[List[str]] = None
    webhook_url: Optional[str] = None
