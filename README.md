# 🛡️ AI Firewall — LLM Gateway Firewall System

<p align="center">
  <strong>AI 大模型网关防火墙</strong> — 位于客户端与大语言模型 (LLM) 之间的安全代理层，提供请求/响应的护栏检测与策略管控。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/fastapi-0.115-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/react-18-61dafb.svg" alt="React 18">
  <img src="https://img.shields.io/badge/litellm-1.50-orange.svg" alt="LiteLLM">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/i18n-zh_CN_|_en_US-lightgrey.svg" alt="i18n">
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Request Flow](#-request-flow)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Plugin System](#-plugin-system)
- [Guardrail Protocol](#-guardrail-protocol)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

AI Firewall is a production-ready **LLM Gateway Firewall** that sits between your application and LLM providers (OpenAI, Azure, Anthropic, local models, etc.). It proxies all API calls through a configurable chain of **guardrails** that inspect, transform, and filter both incoming requests and outgoing responses.

**Why use a gateway firewall instead of direct LLM calls?**

| Without Firewall | With AI Firewall |
|---|---|
| No PII/secret filtering | Auto-detect & redact sensitive data |
| No content moderation | Pre/post guardrails for compliance |
| Single model lock-in | Route across multiple providers |
| No audit trail | Full request/response logging |
| Hard to manage access | Role-based multi-tenant access control |

---

## ✨ Features

### Core Capabilities

- **🔐 Multi-Tenant User Management** — Three-tier roles (Super Admin / Admin / User) with API Key auth and credit-based billing
- **🗂️ Asset Management** — Register LLM providers, MCP tools, and Memory backends with connection testing
- **🛡️ Pluggable Guardrails** — HTTP-based guardrail services with standard protocol; chainable in serial or parallel
- **🔀 Traffic Orchestration** — Compose assets + guardrails into traffic configs with execution ordering
- **🚦 OpenAI-Compatible Proxy** — `/v1/chat/completions` and `/v1/models` endpoints via LiteLLM
- **📊 Dashboards** — Real-time monitoring with user-level and admin-level views
- **🚨 Alerting** — Custom threshold rules with multi-channel notifications
- **📝 Audit Logs** — Full request/response logging with guardrail hit details

### Guardrail Types

| Category | Examples | Position |
|---|---|---|
| **Privacy** | PII detection (phone, email, ID card, IP, bank card) | Pre / Post |
| **Injection Detection** | Prompt injection, jailbreak attempts | Pre |
| **Compliance** | Content policy, keyword filtering | Pre / Post |
| **Tool Call** | Function call validation, parameter checks | Pre |
| **Output** | Toxicity, bias, format validation | Post |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Client / App                         │
└──────────────┬──────────────────────────────┬────────────┘
               │  Web Console                 │  API Proxy
               ▼                              ▼
┌──────────────────────────┐  ┌────────────────────────────┐
│   React Frontend (:5173) │  │  FastAPI Backend (:8000)    │
│                          │  │                             │
│  ┌────────────────────┐  │  │  ┌───────────────────────┐ │
│  │  Dashboard         │  │  │  │  /api/*   REST API    │ │
│  │  Asset Management  │  │  │  │  /v1/*    Proxy API   │ │
│  │  Guardrail Config  │  │  │  ├───────────────────────┤ │
│  │  Traffic Config    │  │  │  │  Auth Middleware       │ │
│  │  Audit Logs        │  │  │  │  Guardrail Executor    │ │
│  │  Alerts            │  │  │  │  LiteLLM Client        │ │
│  └────────────────────┘  │  │  └───────────────────────┘ │
│                          │  │              │              │
│  Ant Design 5            │  │              ▼              │
│  Zustand + Axios         │  │  ┌───────────────────────┐ │
│  i18next (zh/en)         │  │  │  MySQL 8.0 + Redis 7  │ │
└──────────────────────────┘  │  └───────────────────────┘ │
                              └──────────┬─────────────────┘
                                         │
                              ┌──────────▼─────────────────┐
                              │    Guardrail Services       │
                              │                             │
                              │  ┌───────────────────────┐ │
                              │  │ PII Detection (:8822) │ │
                              │  ├───────────────────────┤ │
                              │  │ Injection Detection   │ │
                              │  ├───────────────────────┤ │
                              │  │ Compliance Check      │ │
                              │  ├───────────────────────┤ │
                              │  │ ... (pluggable)       │ │
                              │  └───────────────────────┘ │
                              └────────────────────────────┘
                                         │
                              ┌──────────▼─────────────────┐
                              │     LLM Providers           │
                              │  OpenAI | Azure | DeepSeek  │
                              │  Anthropic | 阿里 | 百度    │
                              │  Custom / Ollama / vLLM     │
                              └────────────────────────────┘
```

---

## 🔄 Request Flow

```
Client Request
  │  POST /v1/chat/completions (OpenAI-compatible)
  ▼
┌─────────────────────────────────┐
│ 1. API Key Authentication       │  → Resolve user_id & tenant
├─────────────────────────────────┤
│ 2. Model → Asset → Traffic      │  → Match model to user asset,
│    Config Resolution            │    then to traffic config
├─────────────────────────────────┤
│ 3. Pre-Guardrail Chain          │  → Serial or parallel execution
│    ┌─────────────────────────┐  │
│    │ PII Detection           │  │
│    │ Injection Detection     │──├── block → return 403 + log
│    │ Compliance Check        │  │  correct → rewrite messages
│    └─────────────────────────┘  │  pass → continue
├─────────────────────────────────┤
│ 4. Credit Deduction             │  → Check balance, deduct points
├─────────────────────────────────┤
│ 5. LiteLLM Forwarding           │  → Proxy to target LLM provider
├─────────────────────────────────┤
│ 6. Post-Guardrail Chain         │  → Same guardrail logic on
│    (supports streaming)         │    model response
├─────────────────────────────────┤
│ 7. Response + Audit Log         │  → Return to client, persist
└─────────────────────────────────┘  full request/response log
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python 3.10+) |
| **LLM Proxy** | LiteLLM 1.50 — unified multi-provider SDK |
| **Frontend** | React 18 + TypeScript + Vite |
| **UI Library** | Ant Design 5 + ECharts |
| **State Management** | Zustand |
| **HTTP Client** | Axios |
| **Internationalization** | i18next (zh-CN / en-US) |
| **Database** | MySQL 8.0 + SQLAlchemy 2.0 (async) |
| **Cache / Pub-Sub** | Redis 7 |
| **Authentication** | JWT (web) + API Key (proxy) |
| **Infrastructure** | Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- **Python** ≥ 3.10
- **Node.js** ≥ 18
- **MySQL** 8.0+
- **Redis** 7+
- **Docker & Docker Compose** (optional, for infra)

### 1. Start Infrastructure

```bash
# Option A: Using Docker
cd aiguard
docker-compose up -d    # Starts MySQL + Redis

# Option B: Using existing MySQL/Redis
# Update backend/.env with your connection strings
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment config
cp .env.example .env
# Edit .env with your DATABASE_URL, REDIS_URL, JWT_SECRET_KEY

# Start (auto-creates DB tables + default admin account)
python -m app.main
# or: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# API docs available at:
#   http://localhost:8000/docs    (Swagger UI)
#   http://localhost:8000/redoc   (ReDoc)
```

**Default Admin Account:**

| Field | Value |
|---|---|
| Email | `admin@aifirewall.local` |
| Password | `Admin@123` |

> ⚠️ **Change the default password immediately after first login.**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Open http://localhost:5173
```

### 4. Start PII Detection Plugin (Optional)

```bash
cd plugins/in-pii-detection

pip install -r requirements.txt
python main.py    # Starts on port 8822
```

---

## ⚙️ Configuration

All backend configuration is managed via environment variables in `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | MySQL async connection | `mysql+aiomysql://root:***@192.168.3.100:3306/aiguardrail` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing secret | **Change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `SMTP_HOST` | Email server host | `smtp.example.com` |
| `SMTP_PORT` | Email server port | `587` |
| `SMTP_USERNAME` | Email account | — |
| `SMTP_PASSWORD` | Email password | — |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:5173,http://localhost:3000` |
| `RATE_LIMIT_PER_MINUTE` | Web API rate limit | `60` |
| `API_KEY_RATE_LIMIT_PER_MINUTE` | Proxy API rate limit | `100` |
| `DEBUG` | Debug mode | `true` |
| `LOG_LEVEL` | Log level | `INFO` |
| `APP_NAME` | Application name | `AI Firewall` |
| `APP_VERSION` | Version | `1.0.0` |

---

## 🔌 Usage

### Proxy API (OpenAI-Compatible)

After creating an LLM asset and API key in the web console:

```bash
# Chat completions
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <YOUR_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "stream": false
  }'

# List available models
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer <YOUR_API_KEY>"

# Health check
curl http://localhost:8000/v1/health
```

### Quick Setup Workflow (Web Console)

1. **Create an LLM Asset** — Navigate to *Asset Management* → *LLM* → *Create*, fill in provider, base URL, API key, and model names
2. **Register a Guardrail** — Navigate to *Guardrail Management* → *Create*, enter the guardrail service endpoint (e.g., `http://localhost:8822/detect`)
3. **Create a Traffic Config** — Navigate to *Traffic Config* → *Create*, select the asset and guardrails, arrange execution order
4. **Generate an API Key** — In *Profile* → *API Keys*, create a key for proxy access
5. **Test** — Use the curl commands above or the built-in test tools

### Code Examples

**Python:**
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="<YOUR_API_KEY>",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

**Node.js:**
```javascript
const response = await fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <YOUR_API_KEY>',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: 'Hello!' }],
  }),
});
const data = await response.json();
console.log(data.choices[0].message.content);
```

---

## 📡 API Reference

### Authentication Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | — | User login |
| `POST` | `/api/auth/register` | — | User registration |
| `GET` | `/api/auth/activate` | — | Account activation |
| `POST` | `/api/auth/refresh` | — | Refresh JWT token |
| `POST` | `/api/auth/forgot-password` | — | Request password reset |
| `POST` | `/api/auth/reset-password` | — | Reset password |

### Asset Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/assets?type=llm` | JWT | List assets |
| `POST` | `/api/assets` | JWT | Create asset |
| `GET` | `/api/assets/{id}` | JWT | Asset detail |
| `PUT` | `/api/assets/{id}` | JWT | Update asset |
| `DELETE` | `/api/assets/{id}` | JWT | Delete asset |
| `POST` | `/api/assets/{id}/test` | JWT | Test connectivity |
| `POST` | `/api/assets/{id}/toggle` | JWT | Enable / disable |

### Guardrail Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/guardrails` | JWT | List guardrails |
| `POST` | `/api/guardrails` | JWT | Create guardrail |
| `GET` | `/api/guardrails/{id}` | JWT | Guardrail detail |
| `PUT` | `/api/guardrails/{id}` | JWT | Update guardrail |
| `DELETE` | `/api/guardrails/{id}` | JWT | Delete guardrail |
| `POST` | `/api/guardrails/{id}/test` | JWT | Test guardrail |
| `POST` | `/api/guardrails/{id}/toggle` | JWT | Enable / disable |

### Traffic Config Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/traffic-configs` | JWT | List traffic configs |
| `POST` | `/api/traffic-configs` | JWT | Create config |
| `GET` | `/api/traffic-configs/{id}` | JWT | Config detail |
| `PUT` | `/api/traffic-configs/{id}` | JWT | Update config |
| `DELETE` | `/api/traffic-configs/{id}` | JWT | Delete config |

### Proxy Gateway (OpenAI-Compatible)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/chat/completions` | API Key | Chat completions |
| `GET` | `/v1/models` | API Key | Model list |
| `GET` | `/v1/health` | — | Health check |

### Monitoring & Admin

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/logs` | JWT | Request logs |
| `GET` | `/api/logs/{id}` | JWT | Log detail with guardrail results |
| `GET` | `/api/user/dashboard/stats` | JWT | User dashboard |
| `GET` | `/api/admin/dashboard/stats` | JWT+Admin | Admin dashboard |
| `GET` | `/api/alert-rules` | JWT | Alert rules list |
| `POST` | `/api/alert-rules` | JWT | Create alert rule |
| `GET` | `/api/alerts` | JWT | Alert events |
| `GET` | `/api/alerts/unread-count` | JWT | Unread alert count |
| `GET` | `/api/billing/consumption` | JWT | Consumption history |
| `POST` | `/api/billing/recharge` | JWT | Credit recharge |
| `GET` | `/api/admin/users` | JWT+Admin | User management |
| `GET` | `/api/admin/settings` | JWT+SuperAdmin | System settings |

---

## 📁 Project Structure

```
aiguard/
├── backend/                         # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                  # Application entry point
│   │   ├── config.py                # Env-based configuration
│   │   ├── database.py              # MySQL + Redis connection pools
│   │   ├── logging_config.py        # Logging setup
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   └── __init__.py          # User, Asset, Guardrail, Traffic, Log, Alert
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   └── __init__.py
│   │   ├── api/                     # REST API route handlers
│   │   │   ├── auth.py              # /api/auth/*
│   │   │   ├── assets.py            # /api/assets/*
│   │   │   ├── guardrails.py        # /api/guardrails/*
│   │   │   ├── traffic.py           # /api/traffic-configs/*
│   │   │   ├── logs.py              # /api/logs/*
│   │   │   ├── dashboard.py         # /api/dashboard/*
│   │   │   ├── alerts.py            # /api/alerts/*
│   │   │   ├── billing.py           # /api/billing/*
│   │   │   ├── users.py             # /api/admin/users/*
│   │   │   └── settings.py          # /api/admin/settings
│   │   ├── gateway/                 # /v1 proxy gateway
│   │   │   ├── __init__.py          # Guardrail execution engine
│   │   │   ├── proxy.py             # Chat completions + models endpoint
│   │   │   └── guard_executor.py    # Per-guardrail HTTP call handler
│   │   ├── middleware/
│   │   │   ├── __init__.py          # Middleware registry
│   │   │   └── auth.py              # JWT + API Key authentication
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── security.py          # Password hashing, JWT, API key gen
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
├── frontend/                        # React 18 + TypeScript frontend
│   ├── src/
│   │   ├── main.tsx                 # Vite entry
│   │   ├── App.tsx                  # Router + layout
│   │   ├── i18n.ts                  # i18next configuration
│   │   ├── api/                     # Axios API clients
│   │   │   ├── client.ts            # Axios instance + interceptors
│   │   │   ├── auth.ts
│   │   │   ├── assets.ts
│   │   │   ├── guardrails.ts
│   │   │   ├── traffic.ts
│   │   │   ├── logs.ts
│   │   │   ├── dashboard.ts
│   │   │   ├── alerts.ts
│   │   │   └── users.ts
│   │   ├── stores/                  # Zustand state management
│   │   │   ├── authStore.ts
│   │   │   └── notificationStore.ts
│   │   ├── components/
│   │   │   └── Layout/              # AppLayout, Sidebar, TopBar
│   │   ├── pages/
│   │   │   ├── auth/                # Login, Register, ForgotPassword, ResetPassword
│   │   │   ├── user/                # Dashboard, Assets, Guardrails, Traffic, Billing,
│   │   │   │                        # Alerts, Logs, ApiKeys
│   │   │   └── admin/               # Users, Settings, Admin Dashboard
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript type definitions
│   │   └── styles/
│   │       └── global.css
│   ├── public/
│   │   └── locales/                 # i18n translation files (zh-CN, en-US)
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── plugins/                         # Standalone guardrail services
│   └── in-pii-detection/            # PII detection guardrail
│       ├── main.py                  # FastAPI service on port 8822
│       ├── requirements.txt
│       └── README.md
├── docker-compose.yml               # MySQL 8.0 + Redis 7
├── docs.md                          # Full technical specification
├── PLAN.md                          # Implementation plan
└── README.md
```

---

## 🧩 Plugin System

AI Firewall supports pluggable guardrail services via a standard HTTP protocol. Each guardrail is a standalone service that the gateway calls during request processing.

### Built-in Plugin: PII Detection

Located at `plugins/in-pii-detection/`, this guardrail detects and handles Personally Identifiable Information:

| Pattern | Examples |
|---|---|
| Phone number | `13812345678` |
| Email address | `test@example.com` |
| ID card (CN) | `110101199001011234` |
| IPv4 address | `192.168.1.1` |
| Bank card | `6222021234567890` |
| Physical address | 北京市海淀区中关村大街1号 |

```bash
# Start the PII detection service
cd plugins/in-pii-detection
pip install -r requirements.txt
python main.py    # → http://localhost:8822
```

### Writing Custom Guardrails

A guardrail must implement:

- **`POST /detect`** — Receive a standard guardrail request, return a verdict
- **`GET /health`** — Return `{"status": "ok"}`

See the [Guardrail Protocol](#-guardrail-protocol) section below for the request/response format.

---

## 🔗 Guardrail Protocol

### Request (sent by the gateway to the guardrail service)

```json
{
  "request_id": "req_abc123",
  "user_id": "user_xyz",
  "domain": "llm",
  "position": "pre",
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "My phone is 13812345678"}
  ],
  "metadata": {},
  "ext_params": {
    "detect_patterns": ["phone", "email"],
    "hit_action": "block"
  }
}
```

### Response (returned by the guardrail service)

```json
{
  "verdict": "block",
  "reason": "Detected 1 sensitive item: 13812345678",
  "confidence": 0.95,
  "matched_rules": [
    {
      "rule": "phone_pattern",
      "location": "messages[0].content",
      "matched": "13812345678"
    }
  ],
  "corrected_content": "My phone is 138****5678",
  "action_suggested": "block"
}
```

### Verdict Values

| Verdict | Behavior |
|---|---|
| `pass` | Allow through; continue to next guardrail or normal flow |
| `block` | Immediately reject; return 403 + log |
| `correct` | Replace content with `corrected_content`; continue |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/my-feature`
3. **Commit** your changes: `git commit -m "feat: add my feature"`
4. **Push**: `git push origin feat/my-feature`
5. Open a **Pull Request**

### Development Guidelines

- Backend: Follow PEP 8; use type hints; add docstrings for public APIs
- Frontend: Use TypeScript; follow the existing component patterns
- Guardrails: Implement the standard HTTP protocol (see [Guardrail Protocol](#-guardrail-protocol))
- Commits: Use [Conventional Commits](https://www.conventionalcommits.org/) format

### Adding a New Guardrail

1. Create a directory under `plugins/<guardrail-name>/`
2. Implement `POST /detect` and `GET /health` endpoints
3. Add a `README.md` with usage instructions
4. Register the guardrail in the web console

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ❤️ using FastAPI, React, LiteLLM, and Ant Design</sub>
</p>
