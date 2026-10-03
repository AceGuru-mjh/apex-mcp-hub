# Apex MCP Hub

**Apex Agent 官方 MCP 服务器仓库** —— 50 台经真实验证的服务器、15 个分类，沙箱（PRoot Ubuntu 内 npx/uvx）与远端（HTTP）双形态，从应用内「市场 → MCP → 官方 MCP 仓库」安装、配置、启动。

[English](#english) below.

## v2 重组说明（2026-10）

1. **并入宿主内置目录**：Android-Guru-Agent 的 `assets/mcp_catalog`（42 条精选目录）中 32 台迁入本仓库，APK 不再随包分发——市场安装即真实下载；
2. **修复两个坏包**：原 `fetch`（@modelcontextprotocol/server-fetch）与 `time`（@modelcontextprotocol/server-time）指向**不存在的 npm 包**，已分别修复为 `@kazuph/mcp-fetch`（node 纯 JS）与 `uvx mcp-server-time`（官方 Python 形态）；
3. **新增 10 台**（端点与包名逐一经 npm registry / PyPI / HTTP initialize 握手验证）：microsoft-learn、context7-remote、amap（高德官方）、firecrawl、paper-search、mongodb、supabase、duckdb、neon、elasticsearch；
4. **全目录分类**：新增 `category` 字段（15 类，前向兼容——App 忽略未知字段），`categories` 顶层统计表随索引分发；
5. 丢弃 2 台在 Android 上不可用的形态（docker run 的 github 与 docker-gateway），GitHub 改用 npx 官方 `server-github`。

## 目录矩阵（50 台 · 15 类）

| 类 | 数 | 服务器 |
|---|---|---|
| official 官方参考实现 | 7 | fs-sandbox、memory-sandbox、everything-sandbox、sequential-thinking、fetch、fetch-python、time |
| docs 文档与知识 | 5 | context7、context7-remote、microsoft-learn、deepwiki、paper-search |
| web-search 网络搜索 | 6 | brave-search、tavily、exa、kagi、duckduckgo、firecrawl |
| browser 浏览器自动化 | 4 | playwright、puppeteer、chrome-devtools、browserbase |
| database 数据库 | 9 | sqlite、postgres、mongodb、supabase、duckdb、neon、elasticsearch、motherduck、dbhub |
| git Git 与代码托管 | 3 | git、server-github、gitlab |
| cloud 云平台 | 2 | cloudflare、kubernetes |
| observability 可观测性 | 2 | sentry、grafana |
| productivity 效率工具 | 3 | notion、obsidian、linear |
| desktop 桌面控制 | 2 | desktop-commander、commands |
| communication 通信协作 | 2 | server-slack、slack-remote |
| location 地图位置 | 2 | google-maps、amap |
| finance 金融支付 | 1 | stripe |
| design 设计 | 1 | figma-context |
| data 数据源 | 1 | gdrive |

`scope` 分布：`coding` 26 / `agent` 13 / `all` 11 —— 市场按工位分级过滤。

## 仓库结构

```
index.json              # 注册表（apex-mcp-hub-v1）：50 台服务器完整配置内联 + categories 统计 + changelog
scripts/build_index.py  # 重建器（从宿主 mcp_catalog + 新增清单生成 index.json）
scripts/validate.py     # 校验器（CI 用；--online 开启包存在性 + HTTP 握手冒烟）
.github/workflows/validate.yml
```

单文件设计：MCP 配置极小（约 800B/条），完整内联在 `index.json` 的 `servers[]` 里，App 一次拉取即可渲染完整目录。

## 条目格式

```json
{
  "name": "amap",
  "description": "高德地图官方 MCP：地理编码/POI 搜索/路线规划/天气……",
  "transport": "STDIO",
  "command": "npx",
  "args": ["-y", "@amap/amap-maps-mcp-server"],
  "env": {},
  "runInSandbox": true,
  "enabled": false,
  "scope": "agent",
  "requiresRootfs": true,
  "vendor": "amap",
  "tags": ["maps", "china", "routing"],
  "category": "location",
  "homepage": "https://lbs.amap.com/api/mcp-server/gettingstarted",
  "envSchema": [{"key": "AMAP_MAPS_API_KEY", "required": true, "description": "……"}],
  "notes": "国内地图场景对 google-maps 的互补。"
}
```

| 字段 | 说明 |
|---|---|
| `transport` | `STDIO`（本地子进程）/ `HTTP`（远端流式） |
| `command` + `args` + `env` | STDIO 启动命令（`npx -y <pkg>` 或 `uvx <mod>`；uvx 需 rootfs 内 python+uv） |
| `runInSandbox` / `requiresRootfs` | `true` = PRoot Ubuntu 沙箱内启动（Android 无宿主 node/python），需先装 rootfs |
| `enabled` | 安装初始态恒 `false` —— **安装 ≠ 启动**（学习 opencode 的配置门控） |
| `scope` | `agent` / `coding` / `all`（工位分级过滤） |
| `category` | 15 类词表之一（v2 新增，前向兼容） |
| `envSchema` | 需要的环境变量声明（key/required/description）——供安装表单/配置引导渲染（前向兼容字段） |

## CI 校验（GitHub Actions）

每次 push / PR 执行 `validate.yml` 双 job：

1. **Index Schema & Entries**：schema / name 唯一 / transport↔字段一致 / enabled 恒 false / requiresRootfs 与形态一致 / category 词表与统计勾稽 / envSchema 完整性 / 2MB 红线 / 凭据泄漏扫描；
2. **Package & Endpoint Reachability**：全部 npx 包在 npm registry 存在、uvx 模块在 PyPI 存在、HTTP 端点 initialize 握手（2xx 通过；401/403 = OAuth 门控视为存活）+ main 分支 raw URL 可达性。另有每周一例行巡检（schedule），坏包/死端点自动暴露。

## 安装/启动语义（学习 opencode 的配置门控）

1. **安装**：市场点「安装」→ 写入 `mcp_servers.json`（enabled=false，只装不跑）；
2. **配置**：每台服务器都有「配置」入口（作用域 / 启停 / 连接 / 环境变量）；
3. **启动**：点「启动」→ 真实连接（进程 fork + JSON-RPC initialize + tools/list 发现），进度可见；
4. **斜杠门控**：只有「已安装且正在运行」的 MCP 才出现在聊天输入框的 `/mcp:` 斜杠菜单。

## 收录约定

- 只收录**开源、可验证**的 MCP 服务器（官方实现优先）；
- STDIO 条目优先 node 纯 JS（arm64 兼容、无原生模块），Python 形态走 uvx；
- 新服务器提 PR：`index.json` 的 `servers[]` 增加条目（或改 `scripts/build_index.py` 后重建），CI 全绿即合并；
- 远端（HTTP）条目必须可匿名或自带 OAuth 授权流程。

---

# English

**Official MCP server repository for Apex Agent** — 50 verified servers across 15 categories, sandbox (npx/uvx inside PRoot Ubuntu) and remote (streamable HTTP) forms, installable / configurable / startable from the in-app Market.

**v2 reorg (Oct 2026)**: absorbed 32 servers from the Android-Guru-Agent bundled catalog (the APK no longer ships them — market installs now truly download from this repo); fixed `fetch`/`time` entries that pointed to **non-existent npm packages**; added 10 new servers, each verified via npm/PyPI registry lookups and live HTTP `initialize` handshakes (microsoft-learn, context7-remote, amap, firecrawl, paper-search, mongodb, supabase, duckdb, neon, elasticsearch); categorized everything with a forward-compatible `category` field plus a `categories` stats legend; dropped 2 docker-based entries that cannot run on Android.

CI runs on every push/PR: schema & consistency validation, plus an online smoke job that verifies every npm/PyPI package still exists and every HTTP endpoint still handshakes (401/403 counts as alive — OAuth-gated), with a weekly scheduled re-check to catch dead packages early. Install writes `enabled=false` (install ≠ start); only installed **and running** servers appear in the chat `/mcp:` slash menu.

Contributions: PR adding an entry to `servers[]` in `index.json`. Open-source, verifiable servers only.
