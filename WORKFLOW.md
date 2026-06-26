# WORKFLOW.md — L3 阶段协议

每个 Phase 必须**所有测试绿灯**后才能进入下一阶段。Phase 之间不跳跃、不并行。

---

## Phase 0 — Bootstrap

**目标**：建立可运行的项目骨架。

**任务清单**：
- [ ] 创建 `pyproject.toml`（包名 `scm-mcp-server`，入口 `scm_mcp_server.server:main`）
- [ ] 创建目录骨架（见 CLAUDE.md 目录约定）
- [ ] 创建 `.env.example`（含全部环境变量占位符）
- [ ] 创建软链 `openapi-specs -> ../pan.dev/openapi-specs`（或在 README 说明路径）
- [ ] `scm_mcp_server/server.py` 可启动：读取环境变量，缺失时打印清晰错误，不 crash

**完成标志**：
```bash
pip install -e ".[dev]"          # 无报错
python -m scm_mcp_server         # 打印 "SCM MCP Server starting..." 或明确的缺失变量错误
```

---

## Phase 1 — Auth

**目标**：实现 OAuth2 token 获取与缓存。

**任务清单**：
- [ ] 实现 `auth.py`：
  - `async get_token() -> str`
  - 内存缓存（`_token`, `_expires_at`）
  - 到期前 60 s 自动刷新
  - 失败时抛出带明确信息的异常
- [ ] 编写 `tests/test_auth.py`：
  - mock `httpx.AsyncClient.post`
  - 验证首次调用发起请求
  - 验证第二次调用命中缓存（不发起请求）
  - 验证 token 过期后重新获取

**完成标志**：
```bash
pytest tests/test_auth.py -v     # 全部 PASSED
```

---

## Phase 2 — Client

**目标**：封装 httpx，统一注入 auth header 与 error handling。

**任务清单**：
- [ ] 实现 `client.py`：
  - `get_client() -> SCMClient`（单例）
  - 自动调用 `auth.get_token()` 注入 Bearer header
  - `base_url` 来自 `SCM_BASE_URL` 环境变量
  - `request(method, path, **kwargs) -> dict`
  - HTTP 4xx/5xx → 抛出 `SCMAPIError`（携带 status + detail）
  - httpx timeout / connect error → 抛出 `SCMAPIError`
- [ ] 编写 `tests/test_client.py`：
  - 用 `respx` mock HTTP 响应
  - 验证 Bearer header 正确注入
  - 验证 400/401/403/404/500 → `SCMAPIError`
  - 验证 timeout → `SCMAPIError`

**完成标志**：
```bash
pytest tests/test_client.py -v   # 全部 PASSED
```

---

## Phase 3 — Tools

**目标**：实现全部 MCP tool，注册到 server.py。

**子阶段顺序**（逐一完成，逐一测试）：

### Phase 3a — Objects
- [ ] 实现 `tools/objects.py`（见 DESIGN.md Group 1 全部 tool）
- [ ] 注册到 `server.py`
- [ ] `tests/test_tools.py` 中添加 objects 测试（mock client）

### Phase 3b — Security
- [ ] 实现 `tools/security.py`（见 DESIGN.md Group 2 全部 tool）
- [ ] 注册到 `server.py`
- [ ] `tests/test_tools.py` 中添加 security 测试

### Phase 3c — Incidents
- [ ] 实现 `tools/incidents.py`（见 DESIGN.md Group 3 全部 tool）
- [ ] 注册到 `server.py`
- [ ] `tests/test_tools.py` 中添加 incidents 测试

**完成标志**：
```bash
pytest tests/test_tools.py -v    # 全部 PASSED
mcp dev scm_mcp_server/server.py # Inspector 能列出所有 tool（见下方 tool 数量）
```

预期 tool 数量：`scm_list_addresses`、`scm_get_address`、`scm_create_address`、`scm_update_address`、`scm_delete_address`、`scm_list_address_groups`、`scm_list_services`、`scm_list_tags`、`scm_list_security_rules`、`scm_get_security_rule`、`scm_create_security_rule`、`scm_update_security_rule`、`scm_delete_security_rule`、`scm_move_security_rule`、`scm_search_incidents`、`scm_get_incident` — **共 16 个**。

---

## Phase 4 — Integration（需真实凭据）

**目标**：端到端冒烟验证。

**任务清单**：
- [ ] 配置 `.env` 填入真实凭据
- [ ] 运行 `mcp dev scm_mcp_server/server.py`
- [ ] 在 Inspector 调用以下 tool 验证响应合法：
  - `scm_list_addresses(folder="Shared", limit=5)` → 返回 `{data, total, ...}`
  - `scm_search_incidents(pagination={page_size: 5, page_number: 1})` → 返回 `{header, data}`
  - `scm_list_security_rules(folder="Shared")` → 返回 `{data, total, ...}`

**完成标志**：上述三个调用均返回 200 且 JSON 结构与 DESIGN.md 出参一致。

---

## Phase 5 — Packaging

**目标**：完善文档与注册配置，可交付。

**任务清单**：
- [ ] 完善 `README.md`（见 README 内容大纲）
- [ ] 验证 Claude Desktop 注册片段可用
- [ ] 验证 Cursor MCP 注册片段可用
- [ ] 可选：添加 `Dockerfile`
- [ ] 运行完整测试套件确认无回归：

```bash
pytest -v                        # 全部 PASSED
```

**完成标志**：按 README 操作的新用户能在 10 分钟内完成安装并在 Claude Desktop 里看到 16 个 `scm_*` tool。

---

## 快速状态检查命令

```bash
# 查看当前测试状态
pytest -v --tb=short

# 列出已注册的 tool
python -c "
import asyncio
from scm_mcp_server.server import mcp
print([t.name for t in mcp.list_tools()])
"

# 检查 token 获取（需配置 .env）
python -c "
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
from scm_mcp_server.auth import get_token
print(asyncio.run(get_token())[:20], '...')
"
```
