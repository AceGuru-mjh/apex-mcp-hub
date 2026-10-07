# Apex MCP Hub

**Apex Agent 官方 MCP 服务器仓库** —— 101 台经真实验证的服务器、19 个分类，沙箱（PRoot Ubuntu 内 npx/uvx）与远端（HTTP）双形态，从应用内「市场 → MCP → 官方 MCP 仓库」安装、配置、启动。

> **v2.3 逆向工程独立成类**：新增 `reverse-engineering` 逆向工程类（15 台），security 中 10 台逆向工具迁入，security 聚焦攻防与情报；新增 7 台实测服务器（reversecore / mitmproxy / gdb / cyberchef / mobsf / cve / metasploit），总量 94 → 101 台。

[English](#english) below.

## v2.3 逆向工程独立成类与扩容说明（2026-10）

1. **逆向工程独立成类**：新增 `reverse-engineering`（18 → 19 类），把 security 类中与「逆向分析」而非「攻防情报」相关的 10 台迁入——静态 7（ghidra、ida-pro、radare2、binary-ninja、jadx、apktool、capstone）、动态 2（frida、android-mcp-server）、取证 1（volatility）；security 类保留攻防与情报定位（semgrep、shodan、nmap、burp）；
2. **新增 7 台**（npm/PyPI registry 逐一 HTTP 200 实测，安装命令均取自官方 README）：
   - **逆向 5**：`reversecore`（PyPI reversecore-mcp，151 工具一体化逆向套件，206★）、`mitmproxy`（PyPI mitmproxy-mcp，抓包检索/改写重放/TLS 指纹伪装/协议逆向，125★）、`gdb`（PyPI gdb-mcp，GNU 调试器 native 动态调试）、`cyberchef`（npm cyberchef-mcp，GCHQ 504 项数据变换解码）、`mobsf`（clone 形态，移动安全框架 APK/IPA SAST+DAST）；
   - **安全 2**：`cve`（npm cve-mcp，41 工具 / 11 数据源漏洞情报聚合）、`metasploit`（PyPI metasploit-mcp，授权渗透测试框架，需 msfrpcd）；
3. **分类勾稽**：reverse-engineering 15 台、security 6 台，`categories` 统计与 `scripts/validate.py` / `build_index.py` 词表同步更新（19 类）；
4. 沿用验证铁律：本地 `validate.py` + `validate.py --online`（npm/PyPI 包存在性 + HTTP 握手）全部通过；mobsf 为 clone 形态（notes 标注 MobSF 实例依赖），metasploit 仅限授权测试场景。

## v2 重组说明（2026-10）

1. **并入宿主内置目录**：Android-Guru-Agent 的 `assets/mcp_catalog`（42 条精选目录）中 32 台迁入本仓库，APK 不再随包分发——市场安装即真实下载；
2. **修复两个坏包**：原 `fetch`（@modelcontextprotocol/server-fetch）与 `time`（@modelcontextprotocol/server-time）指向**不存在的 npm 包**，已分别修复为 `@kazuph/mcp-fetch`（node 纯 JS）与 `uvx mcp-server-time`（官方 Python 形态）；
3. **新增 10 台**（端点与包名逐一经 npm registry / PyPI / HTTP initialize 握手验证）：microsoft-learn、context7-remote、amap（高德官方）、firecrawl、paper-search、mongodb、supabase、duckdb、neon、elasticsearch；
4. **全目录分类**：新增 `category` 字段（15 类，前向兼容——App 忽略未知字段），`categories` 顶层统计表随索引分发；
5. 丢弃 2 台在 Android 上不可用的形态（docker run 的 github 与 docker-gateway），GitHub 改用 npx 官方 `server-github`。

## v2.1 扩容说明（2026-10）

1. **主题「编码与完成复杂任务」**：+30 台 → 80 台（15 → 18 类），编码/开发相关 18 台——数据库 6（redis、neo4j、qdrant、chroma、influxdb、astra-db）、云 2（aws-iac、aws-billing）、可观测性 2（prometheus、datadog）、文档 3（arxiv、aws-docs、wikipedia）、开发效率 5（apifox、gradle、jetbrains、mcp-remote、swagger）；
2. **新增三类**：`devtools 开发效率`、`security 安全`、`ai-ml 人工智能`（`categories` 顶层表已带中文 label 与统计；App 端前向兼容）；
3. **验证铁律**：30 台全部实测可安装——npm 包经 registry.npmjs.org、PyPI 模块经 pypi.org 逐一确认 HTTP 200；候选池 9 个名称未过验证或已弃用（@redis/mcp-redis、@clickhouse/mcp-server、@neo4j/neo4j-mcp-server、@snyk/mcp-server、ansible-doc-mcp-server、memgraph-mcp-server、arangodb-mcp-server、mcp.quickchart.io 端点、hf-mcp 非 HuggingFace 官方）——分别换用官方等价包（PyPI redis-mcp-server / mcp-neo4j-cypher / npm @gongrzhe/quickchart-mcp-server 等）或淘汰；awslabs 已弃用的 cdk/terraform/cost-explorer 换用活跃后继 aws-iac / aws-billing；
4. 其余 12 台：效率 6（atlassian、excel、office-word、pandoc、shrimp-task-manager、todoist）、设计 2（blender、quickchart）、通信 1（gmail-autoauth）、搜索 1（omnisearch）、安全 1（semgrep）、AI 1（aws-bedrock-kb）；mcp-pandoc 需 rootfs 预装 pandoc CLI、semgrep 需预装 semgrep CLI、blender 需桌面端 Blender 实例 + 插件（notes 已标注）；
5. `scripts/build_index.py` 重写为自包含「重算与校验工具」：读 index.json 本体重算 categories 统计与 count、按（类目, name）稳定排序，`--check` 只校验不写盘（不再依赖已退役的 ../Android-Guru-Agent mcp_catalog）。

## 目录矩阵（101 台 · 19 类）

| 类 | 数 | 服务器 |
|---|---|---|
| official 官方参考实现 | 4 | fetch、fetch-python、sequential-thinking、time |
| docs 文档与知识 | 8 | arxiv、aws-docs、context7、context7-remote、deepwiki、microsoft-learn、paper-search、wikipedia |
| web-search 网络搜索 | 7 | brave-search、duckduckgo、exa、firecrawl、kagi、omnisearch、tavily |
| browser 浏览器自动化 | 4 | browserbase、chrome-devtools、playwright、puppeteer |
| database 数据库 | 15 | astra-db、chroma、dbhub、duckdb、elasticsearch、influxdb、mongodb、motherduck、neo4j、neon、postgres、qdrant、redis、sqlite、supabase |
| git Git 与代码托管 | 3 | git、gitlab、server-github |
| cloud 云平台 | 4 | aws-billing、aws-iac、cloudflare、kubernetes |
| observability 可观测性 | 4 | datadog、grafana、prometheus、sentry |
| productivity 效率工具 | 9 | atlassian、excel、linear、notion、obsidian、office-word、pandoc、shrimp-task-manager、todoist |
| desktop 桌面控制 | 2 | desktop-commander、commands |
| communication 通信协作 | 3 | gmail-autoauth、server-slack、slack-remote |
| location 地图位置 | 2 | amap、google-maps |
| finance 金融支付 | 1 | stripe |
| design 设计 | 3 | blender、figma-context、quickchart |
| data 数据源 | 1 | gdrive |
| devtools 开发效率 | 9 | android-emulator、apifox、gradle、jetbrains、mcp-inspector、mcp-remote、postman、serena、swagger |
| **reverse-engineering 逆向工程** | 15 | android-mcp-server、apktool、binary-ninja、capstone、cyberchef、frida、gdb、ghidra、ida-pro、jadx、mitmproxy、mobsf、radare2、reversecore、volatility |
| security 安全 | 6 | burp、cve、metasploit、nmap、semgrep、shodan |
| ai-ml 人工智能 | 1 | aws-bedrock-kb |

`scope` 分布：`coding` 66 / `agent` 16 / `all` 19 —— 市场按工位分级过滤。

## 仓库结构

```
index.json              # 注册表（apex-mcp-hub-v1）：101 台服务器完整配置内联 + categories 统计 + changelog
scripts/build_index.py  # 重算与校验工具（自包含：重算 categories 统计与 count 并稳定排序；--check 只校验）
scripts/validate.py     # 校验器（CI 用；--online 开启包存在性 + HTTP 握手冒烟）
.github/workflows/validate.yml
```

单文件设计：MCP 配置极小（约 1KB/条），完整内联在 `index.json` 的 `servers[]` 里，App 一次拉取即可渲染完整目录。

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
| `category` | 19 类词表之一（v2 新增、v2.1 扩至 18 类，v2.3 新增 reverse-engineering，前向兼容） |
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

**Official MCP server repository for Apex Agent** — 101 verified servers across 19 categories, sandbox (npx/uvx inside PRoot Ubuntu) and remote (streamable HTTP) forms, installable / configurable / startable from the in-app Market.

**v2.3 reverse-engineering split (Oct 2026)**: new `reverse-engineering` category (15 servers) — the 10 RE tools previously mixed into `security` (ghidra, ida-pro, radare2, binary-ninja, jadx, apktool, capstone, frida, android-mcp-server, volatility) moved in, while `security` now focuses on offense/intel (semgrep, shodan, nmap, burp). Added 7 new registry-verified servers: reversecore (151-tool all-in-one RE suite), mitmproxy (traffic capture/replay & protocol RE), gdb (native debugging), cyberchef (504 CyberChef operations), mobsf (mobile SAST/DAST), cve (11-source vulnerability intel), and metasploit (authorized pentesting, requires msfrpcd). Total: 94 → 101.

**v2 reorg (Oct 2026)**: absorbed 32 servers from the Android-Guru-Agent bundled catalog (the APK no longer ships them — market installs now truly download from this repo); fixed `fetch`/`time` entries that pointed to **non-existent npm packages**; added 10 new servers, each verified via npm/PyPI registry lookups and live HTTP `initialize` handshakes (microsoft-learn, context7-remote, amap, firecrawl, paper-search, mongodb, supabase, duckdb, neon, elasticsearch); categorized everything with a forward-compatible `category` field plus a `categories` stats legend; dropped 2 docker-based entries that cannot run on Android.

**v2.1 expansion (Oct 2026)**: +30 servers → 80 across 18 categories (new: devtools, security, ai-ml), themed around coding & complex-task completion — 18 dev-related entries (6 databases, 2 cloud + 1 AI, 2 observability, 3 docs, 5 devtools). Every new entry was verified live against npm/PyPI registries (HTTP 200); 9 candidate names that failed registry verification were swapped for official equivalents or dropped, and deprecated awslabs packages were replaced by their active successors (aws-iac / aws-billing).

CI runs on every push/PR: schema & consistency validation, plus an online smoke job that verifies every npm/PyPI package still exists and every HTTP endpoint still handshakes (401/403 counts as alive — OAuth-gated), with a weekly scheduled re-check to catch dead packages early. Install writes `enabled=false` (install ≠ start); only installed **and running** servers appear in the chat `/mcp:` slash menu.

Contributions: PR adding an entry to `servers[]` in `index.json`. Open-source, verifiable servers only.
