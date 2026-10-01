# Apex MCP Hub

**Apex Agent 官方 MCP 服务器仓库** —— 沙箱（PRoot Ubuntu 内 npx）与远端 MCP 服务器目录，从应用内「市场 → MCP → 官方 MCP 仓库」安装、配置、启动。

[English](#english) below.

## 仓库结构

```
index.json    # 注册表（apex-mcp-hub-v1）：全部 MCP 服务器条目（含完整安装配置）
```

单文件设计：MCP 配置极小（几百字节/条），直接内联在 `index.json` 里，App 一次拉取即可渲染完整目录，无需二次请求。

## index.json 格式

```json
{
  "schema": "apex-mcp-hub-v1",
  "count": 8,
  "servers": [
    {
      "name": "fs-sandbox",
      "description": "……",
      "transport": "STDIO",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "env": {},
      "runInSandbox": true,
      "enabled": false,
      "scope": "coding",
      "requiresRootfs": true,
      "vendor": "modelcontextprotocol",
      "tags": ["files", "official"]
    }
  ]
}
```

字段语义：

| 字段 | 说明 |
|---|---|
| `transport` | `STDIO`（本地子进程）/ `HTTP` / `SSE` |
| `command` + `args` + `env` | STDIO 形态的启动命令（如 `npx -y <package>`） |
| `runInSandbox` | `true` = 在 PRoot Ubuntu 沙箱内启动（Android 无宿主 node 环境） |
| `requiresRootfs` | `true` = 需要先在「终端」页安装 Ubuntu rootfs（App 据此展示引导） |
| `scope` | `agent` / `coding` / `all`（工位作用域，市场分级过滤） |
| `enabled` | 安装时的初始启停态（默认 false —— 安装 ≠ 启动，用户在市场里显式启动） |

## 安装/启动语义（学习 opencode 的配置门控）

1. **安装**：市场里点「安装」→ 写入 `mcp_servers.json`（enabled=false，只装不跑）；
2. **配置**：每台服务器都有「配置」入口（作用域 / 启停 / 连接）；
3. **启动**：点「启动」→ 真实连接（进程 fork + JSON-RPC initialize + tools/list 发现），全程启动进度可见；
4. **斜杠门控**：只有「已安装且正在运行」的 MCP 才会出现在聊天输入框的 `/mcp:` 斜杠菜单里 —— 未安装或未运行的不可选用。

## 收录约定

- 只收录**开源、可验证**的 MCP 服务器（官方 reference servers 优先）；
- STDIO 条目优先选 node 纯 JS 实现（arm64 兼容、无原生模块）；
- 远端（HTTP/SSE）条目必须可匿名或自带 key 流程；
- 新服务器提 PR：`index.json` 增加条目即可。

---

# English

**Official MCP server repository for Apex Agent** — sandbox (npx inside PRoot Ubuntu) and remote MCP server catalog, installable / configurable / startable from the in-app Market (Market → MCP → Official Hub).

Single-file design: every entry carries the full install config inline, so one `index.json` fetch renders the whole catalog. Install writes the config as `enabled=false` (install ≠ start); starting performs the real handshake (process spawn + JSON-RPC initialize + tools/list) with live progress. Only installed **and running** servers appear in the chat `/mcp:` slash menu.

Contributions: PR adding an entry to `index.json`. Open-source, verifiable servers only; pure-JS node implementations preferred for arm64 sandbox compatibility.
