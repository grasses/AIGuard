# PII Detection Guardrail Service

前置护栏服务 — 检测并处理用户输入中的个人身份信息 (PII)。

## 功能

| 检测类型 | 匹配模式 | 示例 |
|---------|---------|------|
| 手机号 | 1[3-9]xxxxxxxxx | 13812345678 |
| 邮箱地址 | user@domain.com | test@example.com |
| 身份证号 | 18位中国身份证 | 110101199001011234 |
| IP地址 | IPv4 | 192.168.1.1 |
| 银行卡号 | 16-19位数字 | 6222021234567890 |
| 地址信息 | 含省/市/区/路/号 | 北京市海淀区 |

## 快速启动

```bash
cd plugins/in-pii-detection

# 安装依赖
pip install -r requirements.txt

# 启动服务 (端口 8822)
python main.py
```

## API

### POST /detect — 检测请求

**请求格式** (符合护栏HTTP标准协议):

```json
{
  "request_id": "req_abc123",
  "user_id": "user_xyz",
  "domain": "llm",
  "position": "pre",
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "我的手机号是13812345678，邮箱是test@example.com"}
  ],
  "metadata": {},
  "ext_params": {
    "detect_patterns": ["phone", "email"],
    "hit_action": "block"
  }
}
```

**响应格式**:

拦截 (block):
```json
{
  "verdict": "block",
  "reason": "检测到 2 处敏感信息: 13812345678, test@example.com",
  "confidence": 0.91,
  "matched_rules": [
    {"rule": "phone_pattern", "location": "messages[0].content → content[6:17]", "matched": "13812345678"},
    {"rule": "email_pattern", "location": "messages[0].content → content[22:38]", "matched": "test@example.com"}
  ],
  "corrected_content": "",
  "action_suggested": "block"
}
```

纠偏 (correct):
```json
{
  "verdict": "correct",
  "reason": "检测到敏感信息...",
  "confidence": 0.91,
  "matched_rules": [...],
  "corrected_content": "["我的手机号是138****5678，邮箱是tes****mple.com"]",
  "action_suggested": "correct"
}
```

### GET /health — 健康检查

```json
{"status": "ok", "service": "pii-detection", "version": "1.0.0"}
```

## ext_params 配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `detect_patterns` | string[] | 全部 | 启用的检测模式: phone/email/id_card/ip/bank_card/address |
| `hit_action` | string | "block" | 命中动作: block(拦截) / correct(纠偏) / alert(仅告警) |
| `skip_roles` | string[] | [] | 跳过的消息角色 (如 ["system"]) |
| `scan_roles` | string[] | ["user","assistant","system"] | 扫描的消息角色 |

## 在 AI Firewall 中注册

在护栏管理页面创建新护栏：

| 字段 | 值 |
|------|-----|
| 名称 | PII检测 |
| 类型 | pii |
| 执行域 | LLM |
| 执行位置 | 前置 |
| 端点URL | `http://localhost:8822/detect` |
| 超时 | 3000ms |
| 命中动作 | block 或 correct |
| 扩展参数 | `{"detect_patterns": ["phone", "email", "id_card"], "hit_action": "block"}` |

## 测试

```bash
# 健康检查
curl http://localhost:8822/health

# 检测手机号
curl -X POST http://localhost:8822/detect   -H "Content-Type: application/json"   -d '{
    "messages": [
      {"role": "user", "content": "我的手机号是13812345678"}
    ],
    "metadata": {},
    "ext_params": {"detect_patterns": ["phone"], "hit_action": "block"}
  }'

# 检测邮箱 (纠偏模式)
curl -X POST http://localhost:8822/detect   -H "Content-Type: application/json"   -d '{
    "messages": [
      {"role": "user", "content": "联系我 test@example.com"}
    ],
    "metadata": {},
    "ext_params": {"detect_patterns": ["email"], "hit_action": "correct"}
  }'

# 检测身份证
curl -X POST http://localhost:8822/detect   -H "Content-Type: application/json"   -d '{
    "messages": [
      {"role": "user", "content": "身份证号110101199001011234"}
    ],
    "metadata": {},
    "ext_params": {"detect_patterns": ["id_card"], "hit_action": "block"}
  }'
```
