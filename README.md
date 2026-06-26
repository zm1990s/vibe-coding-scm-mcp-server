# scm-mcp-server

Palo Alto Networks Strata Cloud Manager (SCM) 的 MCP server，通过 stdio 将 SCM REST API 暴露给 Claude、Cursor 等 AI 助手。

## Prerequisites

- Python 3.11+
- SCM 租户凭据：Client ID、Client Secret、TSG ID
  （在 SCM 控制台 → Identity → Service Accounts 创建）

## Install

```bash
git clone <this-repo>
cd scm-mcp-server
pip install -e ".[dev]"
```

## 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入真实凭据
```

`.env` 内容：

```
SCM_CLIENT_ID=your-client-id
SCM_CLIENT_SECRET=your-client-secret
SCM_TSG_ID=your-tsg-id
SCM_BASE_URL=https://api.strata.paloaltonetworks.com   # 可选，此为默认值
```

## 运行

```bash
# 直接运行
python -m scm_mcp_server

# 用 MCP Inspector 调试
mcp dev scm_mcp_server/server.py
```

## 在 Claude Desktop 注册

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "scm": {
      "command": "python",
      "args": ["-m", "scm_mcp_server"],
      "cwd": "/path/to/scm-mcp-server",
      "env": {
        "SCM_CLIENT_ID": "your-client-id",
        "SCM_CLIENT_SECRET": "your-client-secret",
        "SCM_TSG_ID": "your-tsg-id"
      }
    }
  }
}
```

重启 Claude Desktop，在对话框输入 `/tools` 确认 `scm_*` 系列工具已加载。

## 在 Cursor 注册

创建或编辑项目根目录 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "scm": {
      "command": "python",
      "args": ["-m", "scm_mcp_server"],
      "cwd": "/path/to/scm-mcp-server",
      "env": {
        "SCM_CLIENT_ID": "your-client-id",
        "SCM_CLIENT_SECRET": "your-client-secret",
        "SCM_TSG_ID": "your-tsg-id"
      }
    }
  }
}
```

重启 Cursor，在 Composer 中输入 `@scm` 确认工具可用。

## 可用 Tool 列表（共 16 个）

| Tool | 说明 |
|------|------|
| `scm_list_addresses` | 列出地址对象（支持分页/过滤） |
| `scm_get_address` | 按 ID 获取单个地址对象 |
| `scm_create_address` | 创建地址对象 |
| `scm_update_address` | 更新地址对象 |
| `scm_delete_address` | 删除地址对象 |
| `scm_list_address_groups` | 列出地址组 |
| `scm_list_services` | 列出服务对象 |
| `scm_list_tags` | 列出标签 |
| `scm_list_security_rules` | 列出安全策略规则 |
| `scm_get_security_rule` | 按 ID 获取安全规则 |
| `scm_create_security_rule` | 创建安全规则 |
| `scm_update_security_rule` | 更新安全规则 |
| `scm_delete_security_rule` | 删除安全规则 |
| `scm_move_security_rule` | 调整规则顺序（top/bottom/before/after） |
| `scm_search_incidents` | 搜索安全告警（支持过滤/分页） |
| `scm_get_incident` | 按 ID 获取告警详情 |

完整入参/出参说明见 [DESIGN.md](DESIGN.md)。

## 开发与测试

```bash
# 运行全部测试
pytest -v

# 单独运行各模块测试
pytest tests/test_auth.py -v
pytest tests/test_client.py -v
pytest tests/test_tools.py -v
```

开发阶段协议见 [WORKFLOW.md](WORKFLOW.md)。

## OpenAPI 规范

tool 的 schema 来源为 `../pan.dev/openapi-specs/scm/`（相对本仓库父目录）：

```
openapi-specs/scm/
  auth/AuthService.yaml
  config/
    sase/objects/objects-june.yaml
    sase/security/security-services-R2-2026.yaml
    incidents/Unified_SCM_Incident.yaml
  iam/
  ...
```

**禁止修改规范文件**；如需更新请从上游 `pan.dev` 仓库同步。
