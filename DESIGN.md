# DESIGN.md — L2 设计文档

## 架构概览

```
Claude / Cursor
      │  MCP (stdio)
      ▼
 server.py  ──registers──►  tools/*.py
      │                          │
      │                     client.py  (httpx)
      │                          │
      │                      auth.py   (token cache)
      │                          │
      └──────────────────────────►  SCM REST API
```

- **server.py**：MCP stdio loop，注册所有 tool handler。
- **auth.py**：OAuth2 client_credentials，token 内存缓存，到期前 60 s 自动刷新。
- **client.py**：单例 `AsyncClient`，注入 `Authorization: Bearer <token>` 和 `base_url`，统一 HTTP error → MCP error 映射。
- **tools/\*.py**：按资源分组，每个函数对应一个 MCP tool。

---

## Schema 溯源规则

所有 tool 的 `inputSchema` 字段**必须**来自以下 YAML；不得手抄或臆造字段。

| YAML 文件路径 | 涵盖资源 |
|---|---|
| `openapi-specs/scm/config/sase/objects/objects-june.yaml` | Address、AddressGroup、Service、ServiceGroup、Tag、Application 等对象 |
| `openapi-specs/scm/config/sase/security/security-services-R2-2026.yaml` | SecurityRule、DecryptionRule、AntiSpyware/URL/Wildfire profile 等 |
| `openapi-specs/scm/config/incidents/Unified_SCM_Incident.yaml` | Incident 搜索与详情 |
| `openapi-specs/scm/auth/AuthService.yaml` | OAuth2 token（内部使用，不暴露为 tool） |

---

## MCP Tool 清单

### Group 1 — Objects

> **YAML 来源**：`openapi-specs/scm/config/sase/objects/objects-june.yaml`
> **API 前缀**：`/sse/config/v1`

#### `scm_list_addresses`
- **HTTP**：`GET /sse/config/v1/addresses`
- **入参**（均可选）：
  - `folder` string — 容器：文件夹名称
  - `snippet` string — 容器：snippet 名称
  - `device` string — 容器：设备名称
  - `name` string — 按名称过滤
  - `offset` integer — 分页偏移，默认 0
  - `limit` integer — 每页数量，默认 20，最大 200
- **出参**：`{ data: Address[], total: int, limit: int, offset: int }`

#### `scm_get_address`
- **HTTP**：`GET /sse/config/v1/addresses/{id}`
- **入参**：`id` string (required)
- **出参**：Address 对象

#### `scm_create_address`
- **HTTP**：`POST /sse/config/v1/addresses`
- **入参**：`folder`/`snippet`/`device` (one required) + Address request body
  - `name` string (required)
  - `ip_netmask` / `ip_range` / `ip_wildcard` / `fqdn` — 四选一
  - `description` string (optional)
  - `tag` string[] (optional)
- **出参**：Address 对象（含 `id`）

#### `scm_update_address`
- **HTTP**：`PUT /sse/config/v1/addresses/{id}`
- **入参**：`id` (required) + Address request body（同 create，`name` required）
- **出参**：Address 对象

#### `scm_delete_address`
- **HTTP**：`DELETE /sse/config/v1/addresses/{id}`
- **入参**：`id` string (required)
- **出参**：`{ message: "Object deleted successfully" }`

#### `scm_list_address_groups`
- **HTTP**：`GET /sse/config/v1/address-groups`
- **入参**：`folder`/`snippet`/`device`, `name`, `offset`, `limit`
- **出参**：`{ data: AddressGroup[], total, limit, offset }`

#### `scm_list_services`
- **HTTP**：`GET /sse/config/v1/services`
- **入参**：`folder`/`snippet`/`device`, `name`, `offset`, `limit`
- **出参**：`{ data: Service[], total, limit, offset }`

#### `scm_list_tags`
- **HTTP**：`GET /sse/config/v1/tags`
- **入参**：`folder`/`snippet`/`device`, `name`, `offset`, `limit`
- **出参**：`{ data: Tag[], total, limit, offset }`

---

### Group 2 — Security Rules

> **YAML 来源**：`openapi-specs/scm/config/sase/security/security-services-R2-2026.yaml`
> **API 前缀**：`/sse/config/v1`

#### `scm_list_security_rules`
- **HTTP**：`GET /sse/config/v1/security-rules`
- **入参**：
  - `folder` string (required)
  - `position` string — `pre`/`post`（可选）
  - `name` string, `offset` int, `limit` int
- **出参**：`{ data: SecurityRule[], total, limit, offset }`

#### `scm_get_security_rule`
- **HTTP**：`GET /sse/config/v1/security-rules/{id}`
- **入参**：`id` string (required)
- **出参**：SecurityRule 对象

#### `scm_create_security_rule`
- **HTTP**：`POST /sse/config/v1/security-rules`
- **入参**：`folder` (required) + SecurityRule body
  - `name` string (required)
  - `source`/`destination` string[] (required)
  - `application` string[] (required)
  - `service` string[] (required)
  - `action` string — `allow`/`deny`/`drop`/`reset-client`/`reset-server`/`reset-both` (required)
  - `from_`/`to_` string[] — 安全域
  - `profile_setting` object (optional)
  - `log_setting` string (optional)
  - `disabled` boolean (optional)
- **出参**：SecurityRule 对象（含 `id`）

#### `scm_update_security_rule`
- **HTTP**：`PUT /sse/config/v1/security-rules/{id}`
- **入参**：`id` (required) + SecurityRule body
- **出参**：SecurityRule 对象

#### `scm_delete_security_rule`
- **HTTP**：`DELETE /sse/config/v1/security-rules/{id}`
- **入参**：`id` string (required)
- **出参**：`{ message: "Object deleted successfully" }`

#### `scm_move_security_rule`
- **HTTP**：`POST /sse/config/v1/security-rules/{id}:move`
- **入参**：
  - `id` string (required)
  - `destination` string — `top`/`bottom`/`before`/`after` (required)
  - `rulebase` string — `pre`/`post` (required)
  - `destination_rule` string — 当 destination 为 before/after 时必填
- **出参**：`{ message: "Rule moved successfully" }`

---

### Group 3 — Incidents

> **YAML 来源**：`openapi-specs/scm/config/incidents/Unified_SCM_Incident.yaml`
> **API 前缀**：`/incidents/v1`

#### `scm_search_incidents`
- **HTTP**：`POST /incidents/v1/search`
- **入参**：
  - `filter` object (optional)：
    - `rules` array of `{ property: string, operator: string, values: string[] }`
  - `pagination` object (optional)：
    - `page_size` integer
    - `page_number` integer
    - `order_by` string
- **出参**：
  ```json
  {
    "header": { "dataCount": int, "requestId": string, "status": string, "pagination": {...} },
    "data": [ { "incident_id", "title", "severity", "status", "product", "category", ... } ]
  }
  ```

#### `scm_get_incident`
- **HTTP**：`GET /incidents/v1/details/{incident-id}`
- **入参**：`incident_id` string (required)
- **出参**：完整 Incident 对象，包含：
  `incident_id`, `title`, `description`, `severity_id`, `status`, `raised_time`, `updated_time`,
  `remediations`, `alerts`, `resource_context`, `primary_impacted_objects`, `snow_ticket_id` 等 32+ 字段

---

## Auth 设计（内部，不暴露为 tool）

**YAML 来源**：`openapi-specs/scm/auth/AuthService.yaml`

```
POST /auth/v1/oauth2/access_token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={SCM_CLIENT_ID}
&client_secret={SCM_CLIENT_SECRET}
&scope=tsg_id:{SCM_TSG_ID}
```

- 响应：`{ access_token, token_type, expires_in, scope }`
- 缓存策略：内存单例，`issued_at + expires_in - 60s` 后重新获取
- `auth.py` 对外只暴露 `async get_token() -> str`

---

## Error Mapping

| SCM HTTP 状态 | MCP 返回 |
|---|---|
| 400 Bad Request | `error` with SCM error detail |
| 401 Unauthorized | `error` "Authentication failed – check SCM_CLIENT_*" |
| 403 Forbidden | `error` "Insufficient permissions" |
| 404 Not Found | `error` "Resource not found: {id}" |
| 409 Conflict | `error` SCM conflict detail |
| 5xx | `error` "SCM API error {status}: {detail}" |
| httpx timeout | `error` "Request timeout" |
| httpx connect error | `error` "Cannot connect to SCM: {SCM_BASE_URL}" |
