"""
PII Detection Guardrail Service — 前置护栏：检测手机号、邮箱、身份证

符合护栏HTTP服务标准协议：
- 接收 POST 请求，包含 messages / ext_params
- 返回 { verdict, reason, confidence, matched_rules, corrected_content }

启动: python main.py  (默认端口 8822)
测试: curl -X POST http://localhost:8822/detect -H "Content-Type: application/json" -d '{...}'
"""

import re
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Any

app = FastAPI(title="PII Detection Guardrail", version="1.0.0")

# ──────────────────────── Detection Patterns ────────────────────────

# Chinese mobile phone: 1[3-9]xxxxxxxxx
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")

# Email address
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)

# Chinese ID card (18 digits, basic format check)
ID_CARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
)

# IP address
IP_RE = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?!\d)",
)

# Bank card number (16-19 digits)
BANK_CARD_RE = re.compile(r"(?<!\d)\d{16,19}(?!\d)")

# Home address patterns (Chinese)
ADDRESS_RE = re.compile(
    r"(?:省|市|区|县|镇|乡|村|路|街|巷|号|栋|单元|室|楼)",
)

PATTERNS: dict[str, tuple[re.Pattern, str, str]] = {
    "phone":       (PHONE_RE,      "手机号",   "phone_pattern"),
    "email":       (EMAIL_RE,      "邮箱地址", "email_pattern"),
    "id_card":     (ID_CARD_RE,    "身份证号", "id_card_pattern"),
    "ip":          (IP_RE,         "IP地址",   "ip_pattern"),
    "bank_card":   (BANK_CARD_RE,  "银行卡号", "bank_card_pattern"),
    "address":     (ADDRESS_RE,    "地址信息", "address_pattern"),
}

# ──────────────────────── Models ────────────────────────

class GuardrailMessage(BaseModel):
    role: str
    content: str

class GuardrailRequest(BaseModel):
    request_id: str = ""
    user_id: str = ""
    domain: str = "llm"
    position: str = "pre"
    model: str = ""
    messages: List[GuardrailMessage]
    metadata: dict = {}
    ext_params: dict = {}


class MatchedRule(BaseModel):
    rule: str
    location: str
    matched: str


class GuardrailResponse(BaseModel):
    verdict: str          # pass | block | correct
    reason: str = ""
    confidence: float = 0.0
    matched_rules: List[MatchedRule] = []
    corrected_content: str = ""
    action_suggested: str = "pass"


# ──────────────────────── Detection Logic ────────────────────────

def mask_match(match: str, pattern_name: str) -> str:
    """Mask detected PII, preserving first 3 and last 4 characters."""
    if len(match) <= 7:
        return match[0] + "*" * (len(match) - 2) + match[-1]
    return match[:3] + "*" * (len(match) - 7) + match[-4:]


def detect_content(content: str, enabled_patterns: list[str], action: str = "block"):
    """
    Scan content for PII.
    Returns:
      - matched_rules: list of detected patterns
      - corrected_content: masked version (for 'correct' action)
      - highest_confidence: max confidence among matches
    """
    # Default: detect all patterns
    if not enabled_patterns:
        enabled_patterns = list(PATTERNS.keys())

    matched_rules: list[dict] = []
    corrected = content

    for pattern_name in enabled_patterns:
        if pattern_name not in PATTERNS:
            continue
        regex, display_name, rule_id = PATTERNS[pattern_name]
        for match in regex.finditer(content):
            matched_rules.append({
                "rule": rule_id,
                "location": f"content[{match.start()}:{match.end()}]",
                "matched": match.group(),
            })
            # Replace in corrected version
            if action == "correct":
                corrected = corrected.replace(
                    match.group(), mask_match(match.group(), pattern_name), 1
                )

    confidence = min(1.0, len(matched_rules) * 0.3) if matched_rules else 1.0
    if matched_rules:
        confidence = 0.85 + min(0.15, len(matched_rules) * 0.03)

    return matched_rules, corrected, confidence


# ──────────────────────── Routes ────────────────────────

@app.post("/detect")
async def detect(req: GuardrailRequest):
    """
    Main detection endpoint.
    Accepts the standard guardrail request, returns standard response.
    """
    # Read ext_params
    ext = req.ext_params or {}
    detect_patterns = ext.get("detect_patterns", list(PATTERNS.keys()))
    hit_action = ext.get("hit_action", "block")  # block / correct / alert
    skip_roles = ext.get("skip_roles", [])        # skip system messages

    all_matched: list[dict] = []
    corrected_contents: list[str] = []

    for i, msg in enumerate(req.messages):
        # Skip system messages by default
        if msg.role in skip_roles:
            corrected_contents.append(msg.content)
            continue
        if msg.role == "system" and "system" not in ext.get("scan_roles", ["user", "assistant", "system"]):
            corrected_contents.append(msg.content)
            continue

        matched, corrected, _ = detect_content(msg.content, detect_patterns, hit_action)
        for m in matched:
            m["location"] = f"messages[{i}].content → {m['location']}"
        all_matched.extend(matched)
        corrected_contents.append(corrected)

    # Build response
    if not all_matched:
        return {
            "verdict": "pass",
            "reason": "未检测到敏感信息",
            "confidence": 1.0,
            "matched_rules": [],
            "corrected_content": "",
            "action_suggested": "pass",
        }

    # Build reason message
    rule_names = list(set(m["rule"] for m in all_matched))
    matched_values = [m["matched"] for m in all_matched]
    reason = f"检测到 {len(all_matched)} 处敏感信息: {', '.join(matched_values[:5])}"
    if len(all_matched) > 5:
        reason += f" 等{len(all_matched)}处"

    confidence = 0.85 + min(0.15, len(all_matched) * 0.02)

    if hit_action == "correct":
        return {
            "verdict": "correct",
            "reason": reason,
            "confidence": confidence,
            "matched_rules": all_matched,
            "corrected_content": json.dumps(corrected_contents, ensure_ascii=False),
            "action_suggested": "correct",
        }
    elif hit_action == "alert":
        return {
            "verdict": "pass",
            "reason": f"[ALERT] {reason}",
            "confidence": confidence,
            "matched_rules": all_matched,
            "corrected_content": "",
            "action_suggested": "pass",
        }
    else:
        # block (default)
        return {
            "verdict": "block",
            "reason": reason,
            "confidence": confidence,
            "matched_rules": all_matched,
            "corrected_content": "",
            "action_suggested": "block",
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "pii-detection", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "service": "PII Detection Guardrail",
        "version": "1.0.0",
        "endpoints": {
            "detect": "POST /detect",
            "health": "GET /health",
        },
        "supported_patterns": list(PATTERNS.keys()),
        "ext_params": {
            "detect_patterns": "List of patterns to detect (default: all)",
            "hit_action": "block | correct | alert (default: block)",
            "skip_roles": "List of roles to skip (default: [])",
            "scan_roles": "List of roles to scan (default: [user, assistant, system])",
        },
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  PII Detection Guardrail Service")
    print("  Listening on http://0.0.0.0:8822")
    print("  Health:  GET  /health")
    print("  Detect:  POST /detect")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8822, log_level="info")
