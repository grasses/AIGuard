"""SQLAlchemy ORM models for all entities."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float, Text,
    ForeignKey, JSON, Enum as SAEnum, BigInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


def gen_uuid() -> str:
    return uuid.uuid4().hex[:12]


# ──────────────────────── Enums ────────────────────────

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    user = "user"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    locked = "locked"


class AssetType(str, enum.Enum):
    llm = "llm"
    mcp = "mcp"
    memory = "memory"


class Visibility(str, enum.Enum):
    private = "private"
    group = "group"
    public = "public"


class GuardrailDomain(str, enum.Enum):
    llm = "llm"
    mcp = "mcp"
    memory = "memory"


class GuardrailPosition(str, enum.Enum):
    pre = "pre"
    post = "post"


class HitAction(str, enum.Enum):
    alert = "alert"
    block = "block"
    correct = "correct"


class AlertLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class RechargeStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


# ──────────────────────── User ────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    status = Column(SAEnum(UserStatus), default=UserStatus.inactive, nullable=False)
    balance = Column(BigInteger, default=0, nullable=False)  # 积分余额 (分)
    login_failed_count = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    activation_token = Column(String(128), nullable=True)
    reset_token = Column(String(128), nullable=True)
    api_key = Column(String(64), unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="owner", cascade="all, delete-orphan")
    guardrails = relationship("Guardrail", back_populates="owner", cascade="all, delete-orphan")
    traffic_configs = relationship("TrafficConfig", back_populates="owner", cascade="all, delete-orphan")


class ApiKey(Base):
    """User's API keys for /v1 proxy access."""
    __tablename__ = "api_keys"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(128), unique=True, nullable=False)
    key_prefix = Column(String(16), nullable=False)  # First 8 chars for display
    enabled = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="api_keys")


# ──────────────────────── Asset ────────────────────────

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    owner_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(AssetType), nullable=False)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    connectivity = Column(String(20), default="untested")  # untested/healthy/unhealthy
    visibility = Column(SAEnum(Visibility), default=Visibility.private)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # LLM-specific
    provider = Column(String(50), nullable=True)
    protocol = Column(String(50), nullable=True)
    base_url = Column(String(500), nullable=True)
    api_key = Column(Text, nullable=True)  # Encrypted at rest
    model_names = Column(JSON, nullable=True)  # ["gpt-4o", "gpt-4o-mini"]
    max_tokens = Column(Integer, default=4096)
    timeout_seconds = Column(Integer, default=60)
    max_retries = Column(Integer, default=3)
    temperature = Column(Float, default=0.7)
    group_ids = Column(JSON, nullable=True)  # ["group1", "group2"]

    # MCP-specific
    tool_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    endpoint_url = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    authentication_type = Column(String(20), nullable=True)  # bearer/api_key/none
    parameter_schema = Column(JSON, nullable=True)
    required_parameters = Column(JSON, nullable=True)
    response_mapping = Column(JSON, nullable=True)

    # Memory-specific
    index_name = Column(String(100), nullable=True)
    max_tokens_capacity = Column(Integer, nullable=True)
    persist = Column(Boolean, default=False)
    expire_days = Column(Integer, nullable=True)

    owner = relationship("User", back_populates="assets")
    traffic_links = relationship("TrafficAssetLink", back_populates="asset", cascade="all, delete-orphan")


# ──────────────────────── Guardrail ────────────────────────

class Guardrail(Base):
    __tablename__ = "guardrails"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    owner_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    guardrail_type = Column(String(50), nullable=False)  # privacy/compliance/injection/sensitive/pii/jailbreak etc.
    domain = Column(SAEnum(GuardrailDomain), nullable=False)
    position = Column(SAEnum(GuardrailPosition), nullable=False)
    description = Column(Text, nullable=True)
    default_priority = Column(Integer, default=50)
    enabled = Column(Boolean, default=True)

    # HTTP Service config
    endpoint_url = Column(String(500), nullable=False)
    timeout_ms = Column(Integer, default=3000)
    retry_count = Column(Integer, default=0)
    health_check_path = Column(String(200), nullable=True)
    supports_multimodal = Column(Boolean, default=False)

    # Streaming config
    streaming_enabled = Column(Boolean, default=False)
    window_tokens = Column(Integer, default=100)
    window_overlap = Column(Integer, default=20)

    # Hit action
    hit_action = Column(SAEnum(HitAction), nullable=False, default=HitAction.block)
    alert_methods = Column(JSON, nullable=True)  # ["in_app", "email", "webhook"]
    alert_recipients = Column(JSON, nullable=True)  # ["user_id1", "user_id2"]
    webhook_url = Column(String(500), nullable=True)
    correct_template = Column(Text, nullable=True)

    # Matching & Extension
    match_conditions = Column(JSON, nullable=True)
    ext_params = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="guardrails")
    traffic_entries = relationship("TrafficGuardrailEntry", back_populates="guardrail", cascade="all, delete-orphan")


# ──────────────────────── Traffic Config ────────────────────────

class TrafficConfig(Base):
    __tablename__ = "traffic_configs"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    owner_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    execution_mode = Column(String(20), default="serial")  # serial / parallel
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="traffic_configs")
    asset_links = relationship("TrafficAssetLink", back_populates="traffic_config", cascade="all, delete-orphan")
    guardrail_entries = relationship("TrafficGuardrailEntry", back_populates="traffic_config", cascade="all, delete-orphan")


class TrafficAssetLink(Base):
    """Many-to-many: TrafficConfig <-> Asset"""
    __tablename__ = "traffic_asset_links"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    traffic_config_id = Column(String(32), ForeignKey("traffic_configs.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(String(32), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("traffic_config_id", "asset_id"),)

    traffic_config = relationship("TrafficConfig", back_populates="asset_links")
    asset = relationship("Asset", back_populates="traffic_links")


class TrafficGuardrailEntry(Base):
    """Ordered list of guardrails within a traffic config."""
    __tablename__ = "traffic_guardrail_entries"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    traffic_config_id = Column(String(32), ForeignKey("traffic_configs.id", ondelete="CASCADE"), nullable=False)
    guardrail_id = Column(String(32), ForeignKey("guardrails.id", ondelete="CASCADE"), nullable=False)
    position = Column(SAEnum(GuardrailPosition), nullable=False)  # pre / post
    priority = Column(Integer, nullable=False)  # execution order (lower first)
    enabled = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("traffic_config_id", "guardrail_id", "position"),)

    traffic_config = relationship("TrafficConfig", back_populates="guardrail_entries")
    guardrail = relationship("Guardrail", back_populates="traffic_entries")


# ──────────────────────── Request Log ────────────────────────

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    api_key_hash = Column(String(128), nullable=True)
    model = Column(String(100), nullable=False)
    traffic_config_id = Column(String(32), nullable=True)
    asset_id = Column(String(32), nullable=True)

    # Request/Response
    request_messages = Column(JSON, nullable=True)
    request_tokens = Column(Integer, default=0)
    response_content = Column(Text, nullable=True)
    response_tokens = Column(Integer, default=0)

    # Timing
    received_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    latency_ms = Column(Integer, default=0)

    # Status
    status = Column(String(20), default="pending")  # pending / blocked_pre / forwarded / blocked_post / completed / error
    blocked_by = Column(String(100), nullable=True)
    block_reason = Column(Text, nullable=True)

    # Cost
    cost = Column(Float, default=0.0)
    points_consumed = Column(Integer, default=0)

    # Guardrail results
    guardrail_results = Column(JSON, nullable=True)
    # Example: [{"guardrail_id": "xxx", "name": "隐私检测", "verdict": "block", "latency_ms": 45}]

    created_at = Column(DateTime, server_default=func.now())


# ──────────────────────── Alert ────────────────────────

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    metric = Column(String(50), nullable=False)  # block_rate / request_count / latency / error_rate
    condition = Column(String(10), nullable=False)  # gt / lt / gte / lte / eq
    threshold = Column(Float, nullable=False)
    window_minutes = Column(Integer, default=5)
    notify_methods = Column(JSON, default=list)  # ["in_app", "email", "webhook"]
    notify_users = Column(JSON, default=list)
    webhook_url = Column(String(500), nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    rule_id = Column(String(32), ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    level = Column(SAEnum(AlertLevel), default=AlertLevel.warning)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


# ──────────────────────── Billing ────────────────────────

class RechargeOrder(Base):
    __tablename__ = "recharge_orders"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount_points = Column(BigInteger, nullable=False)  # 积分数量
    amount_money = Column(Float, nullable=False)  # 金额 (元)
    status = Column(SAEnum(RechargeStatus), default=RechargeStatus.pending)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)


class PointsConsumption(Base):
    """Points consumption log."""
    __tablename__ = "points_consumption"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_log_id = Column(String(32), nullable=True)
    points = Column(Integer, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# ──────────────────────── System Settings ────────────────────────

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String(32), primary_key=True, default=gen_uuid)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(String(200), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
