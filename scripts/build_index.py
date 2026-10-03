#!/usr/bin/env python3
"""apex-mcp-hub v2 重建器：App mcp_catalog 32 条 + 现有 8 条（修复 fetch/time）
+ 10 台新验证服务器 → 50 台分类目录。

运行前提：Android-Guru-Agent 克隆在 ../Android-Guru-Agent。
输出：index.json（apex-mcp-hub-v1 schema，新增 category/homepage/envSchema 前向兼容字段）。
"""
import json
import os

CATALOG_DIR = "../Android-Guru-Agent/app/src/main/assets/mcp_catalog"
OUT = "index.json"

# ── 分类体系（15 类，标签中文）──
CATEGORY_LABELS = {
    "official": "官方参考实现",
    "docs": "文档与知识",
    "web-search": "网络搜索",
    "browser": "浏览器自动化",
    "database": "数据库",
    "git": "Git 与代码托管",
    "cloud": "云平台",
    "observability": "可观测性",
    "productivity": "效率工具",
    "desktop": "桌面控制",
    "finance": "金融支付",
    "design": "设计",
    "communication": "通信协作",
    "location": "地图位置",
    "data": "数据源",
}

# ── 从 App 目录迁入的 32 台：catalog-id → (category, scope, vendor, [name override]) ──
CATALOG_MAP = {
    # official.json 独有（uvx 官方 Python 形态）
    "fetch-python": ("official", "all", "modelcontextprotocol", None),
    "git": ("git", "coding", "modelcontextprotocol", None),
    # web-search
    "brave-search": ("web-search", "agent", "modelcontextprotocol", None),
    "tavily": ("web-search", "agent", "tavily", None),
    "exa": ("web-search", "agent", "exa-labs", None),
    "kagi": ("web-search", "agent", "kagi", None),
    "duckduckgo": ("web-search", "all", "duckduckgo", None),
    # browser
    "playwright": ("browser", "coding", "microsoft", None),
    "puppeteer": ("browser", "coding", "modelcontextprotocol", None),
    "chrome-devtools": ("browser", "coding", "google", None),
    "browserbase": ("browser", "coding", "browserbase", None),
    # database
    "sqlite": ("database", "coding", "modelcontextprotocol", None),
    "postgres": ("database", "coding", "modelcontextprotocol", None),
    "motherduck": ("database", "coding", "motherduck", None),
    "dbhub": ("database", "coding", "bytebase", None),
    # git / cloud / observability
    "server-github": ("git", "coding", "modelcontextprotocol", None),
    "gitlab": ("git", "coding", "modelcontextprotocol", None),
    "cloudflare": ("cloud", "coding", "cloudflare", None),
    "kubernetes": ("cloud", "coding", "flux159", None),
    "sentry": ("observability", "coding", "sentry", None),
    "grafana": ("observability", "coding", "grafana", None),
    # productivity / desktop / finance / design
    "notion": ("productivity", "agent", "notion", None),
    "obsidian": ("productivity", "agent", "obsidian", None),
    "linear": ("productivity", "coding", "linear", None),
    "desktop-commander": ("desktop", "all", "wonderwhy-er", None),
    "commands": ("desktop", "all", "g0t4", None),
    "stripe": ("finance", "all", "stripe", None),
    "figma-context": ("design", "coding", "glideapps", None),
    # communication / location / data
    "server-slack": ("communication", "agent", "modelcontextprotocol", None),
    "slack-remote": ("communication", "agent", "slack", None),
    "google-maps": ("location", "agent", "modelcontextprotocol", None),
    "gdrive": ("data", "agent", "modelcontextprotocol", None),
}


def from_catalog(entry, category, scope, vendor, name_override):
    """App mcp_catalog 条目 → hub 条目。"""
    http = entry.get("transport") in ("HTTP", "SSE")
    return {
        "name": name_override or entry["id"],
        "description": entry.get("descriptionZh") or entry.get("description", ""),
        "transport": entry.get("transport", "STDIO"),
        **({"url": entry["url"]} if http else {}),
        **({} if http else {
            "command": entry.get("command", "npx"),
            "args": entry.get("args", []),
        }),
        "env": {},
        "runInSandbox": bool(entry.get("sandboxOnly", not http)),
        "enabled": False,
        "scope": scope,
        "requiresRootfs": not http,
        "vendor": vendor,
        "tags": sorted({category, *(entry.get("tags", []) if entry.get("tags") else [])}),
        "category": category,
        "homepage": entry.get("homepage", ""),
        "envSchema": entry.get("envSchema", []),
        "notes": entry.get("notes", ""),
    }


def main():
    # 1) 读 App 目录
    catalog = {}
    for fname in sorted(os.listdir(CATALOG_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(CATALOG_DIR, fname), encoding="utf-8") as fp:
            d = json.load(fp)
        for e in d.get("entries", []):
            catalog[e["id"]] = e

    servers = []

    # 2) 现有 8 台（修复 fetch/time 两个不存在的 npm 包）
    servers += [
        {
            "name": "fs-sandbox",
            "description": "官方文件系统 MCP（沙箱形态）：在 /workspace 作用域内读写文件、建目录、移动与搜索——内置 fs 的 npx 双胞胎。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "modelcontextprotocol",
            "tags": ["files", "official", "workspace"], "category": "official",
            "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
            "envSchema": [{"key": "WORKSPACE", "required": False,
                           "description": "可选：覆盖默认工作区路径（默认 /workspace）"}],
            "notes": "路径参数即允许访问的目录；沙箱形态以 /workspace 为作用域。",
        },
        {
            "name": "memory-sandbox",
            "description": "官方知识图谱记忆 MCP（沙箱形态）：实体/关系/观察的持久化记忆——内置 memory 的 npx 双胞胎。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "agent",
            "requiresRootfs": True, "vendor": "modelcontextprotocol",
            "tags": ["memory", "official", "knowledge-graph"], "category": "official",
            "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
            "envSchema": [],
            "notes": "跨会话记忆外脑；与内置 memory MCP 同源同构。",
        },
        {
            "name": "everything-sandbox",
            "description": "官方测试参考服务器：覆盖 MCP 全能力面（工具/资源/提示词/采样）——验证沙箱 MCP 管线的首选。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "modelcontextprotocol",
            "tags": ["testing", "official", "reference"], "category": "official",
            "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/everything",
            "envSchema": [],
            "notes": "全能力面冒烟测试用。",
        },
        {
            "name": "context7",
            "description": "任何库/框架的最新文档实时检索（Upstash Context7）——对抗训练数据过时，直查现行版本文档。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "upstash",
            "tags": ["docs", "coding", "libraries"], "category": "docs",
            "homepage": "https://github.com/upstash/context7",
            "envSchema": [{"key": "CONTEXT7_API_KEY", "required": False,
                           "description": "可选：更高配额（匿名亦可用）"}],
            "notes": "免沙箱远端形态见 context7-remote。",
        },
        {
            "name": "sequential-thinking",
            "description": "官方顺序思考链服务器：动态分步推理、思路修正与分支——把长链推理从一次性输出变成可回溯的过程。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "all",
            "requiresRootfs": True, "vendor": "modelcontextprotocol",
            "tags": ["reasoning", "official", "thinking"], "category": "official",
            "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking",
            "envSchema": [],
            "notes": "与内置 thinking MCP 互补的官方参考实现。",
        },
        {
            "name": "fetch",
            "description": "网页抓取服务器（node 纯 JS 形态）：URL → 干净 Markdown，内置分页与机器人规避。v2 修复：原 @modelcontextprotocol/server-fetch npm 包不存在，已切换为 @kazuph/mcp-fetch。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@kazuph/mcp-fetch"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "agent",
            "requiresRootfs": True, "vendor": "kazuph",
            "tags": ["web", "fetch", "markdown"], "category": "official",
            "homepage": "https://github.com/kazuph/mcp-fetch",
            "envSchema": [],
            "notes": "官方 Python 形态见 fetch-python（uvx）。",
        },
        {
            "name": "time",
            "description": "官方时间服务器（Python uvx 形态）：当前时间/时区换算与任意格式时间解析。v2 修复：原 @modelcontextprotocol/server-time npm 包不存在，已切换为 uvx mcp-server-time。",
            "transport": "STDIO", "command": "uvx",
            "args": ["mcp-server-time"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "all",
            "requiresRootfs": True, "vendor": "modelcontextprotocol",
            "tags": ["time", "official", "timezone"], "category": "official",
            "homepage": "https://github.com/modelcontextprotocol/servers/tree/main/src/time",
            "envSchema": [],
            "notes": "沙箱需 python + uv（rootfs 内预装）。",
        },
        {
            "name": "deepwiki",
            "description": "DeepWiki 远端 MCP：就任意公开 GitHub 仓库直接提问（架构/实现/用法），免密钥即连的代码理解外脑。",
            "transport": "HTTP",
            "url": "https://mcp.deepwiki.com/mcp",
            "env": {}, "runInSandbox": False, "enabled": False, "scope": "all",
            "requiresRootfs": False, "vendor": "asyncfuncai",
            "tags": ["docs", "github", "remote"], "category": "docs",
            "homepage": "https://github.com/AsyncFuncAI/deepwiki-mcp",
            "envSchema": [],
            "notes": "免沙箱远端形态，零配置。",
        },
    ]

    # 3) App 目录迁入 32 台
    for cid, (cat, scope, vendor, name_ov) in CATALOG_MAP.items():
        if cid not in catalog:
            raise SystemExit(f"catalog entry missing: {cid}")
        servers.append(from_catalog(catalog[cid], cat, scope, vendor, name_ov))

    # 4) 新增 10 台（多源新验证）
    servers += [
        {
            "name": "microsoft-learn",
            "description": "微软官方远端 MCP：检索 Microsoft/Azure 官方文档与代码示例（docs_search / code_sample_search / docs_fetch 三工具流），免密钥直连。",
            "transport": "HTTP",
            "url": "https://learn.microsoft.com/api/mcp",
            "env": {}, "runInSandbox": False, "enabled": False, "scope": "coding",
            "requiresRootfs": False, "vendor": "microsoft",
            "tags": ["docs", "azure", "remote"], "category": "docs",
            "homepage": "https://learn.microsoft.com/azure/developer/azure-mcp/",
            "envSchema": [],
            "notes": "官方托管端点，流式 HTTP，零配置。",
        },
        {
            "name": "context7-remote",
            "description": "Context7 免沙箱远端形态：库文档实时检索的 HTTP 端点，无需 rootfs / npx，装好即连。",
            "transport": "HTTP",
            "url": "https://mcp.context7.com/mcp",
            "env": {}, "runInSandbox": False, "enabled": False, "scope": "all",
            "requiresRootfs": False, "vendor": "upstash",
            "tags": ["docs", "remote", "libraries"], "category": "docs",
            "homepage": "https://github.com/upstash/context7",
            "envSchema": [],
            "notes": "沙箱 npx 形态见 context7。",
        },
        {
            "name": "amap",
            "description": "高德地图官方 MCP：地理编码/逆地理/POI 搜索/路线规划（驾车/步行/公交）/天气查询——中文地点与国内出行场景首选。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@amap/amap-maps-mcp-server"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "agent",
            "requiresRootfs": True, "vendor": "amap",
            "tags": ["maps", "china", "routing"], "category": "location",
            "homepage": "https://lbs.amap.com/api/mcp-server/gettingstarted",
            "envSchema": [{"key": "AMAP_MAPS_API_KEY", "required": True,
                           "description": "高德开放平台 Web 服务 Key（lbs.amap.com 免费申请）"}],
            "notes": "国内地图场景对 google-maps 的互补。",
        },
        {
            "name": "firecrawl",
            "description": "Firecrawl 网页转 Markdown 服务：单页/整站爬取、JS 渲染、结构化抽取——把任意网页变成 LLM 可用的干净数据。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "firecrawl-mcp"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "all",
            "requiresRootfs": True, "vendor": "firecrawl",
            "tags": ["web", "scraping", "crawl"], "category": "web-search",
            "homepage": "https://github.com/firecrawl/firecrawl-mcp-server",
            "envSchema": [{"key": "FIRECRAWL_API_KEY", "required": True,
                           "description": "firecrawl.dev API Key（有免费额度）"}],
            "notes": "与 fetch 的区别：整站爬取 + JS 渲染 + 结构化抽取。",
        },
        {
            "name": "paper-search",
            "description": "学术论文检索服务器（node 形态）：arXiv / PubMed / bioRxiv 多源论文搜索与全文下载链接，写综述查文献的利器。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "paper-search-mcp-nodejs"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "all",
            "requiresRootfs": True, "vendor": "open-science",
            "tags": ["research", "arxiv", "papers"], "category": "docs",
            "homepage": "https://github.com/OpenSciHackathon/paper-search-mcp-nodejs",
            "envSchema": [],
            "notes": "无需 API Key，即装即用。",
        },
        {
            "name": "mongodb",
            "description": "MongoDB 官方 MCP：连接实例/Atlas，查集合、跑聚合管道、分析 schema 与索引。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "mongodb-mcp-server"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "mongodb",
            "tags": ["database", "nosql", "atlas"], "category": "database",
            "homepage": "https://github.com/mongodb-js/mongodb-mcp-server",
            "envSchema": [{"key": "MDB_MCP_CONNECTION_STRING", "required": True,
                           "description": "mongodb:// 或 mongodb+srv:// 连接串"}],
            "notes": "官方 npm 分发。",
        },
        {
            "name": "supabase",
            "description": "Supabase 官方 MCP：项目管理、表结构/迁移、RLS 策略与 SQL 查询——serverless Postgres 全栈工作台。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@supabase/mcp-server-supabase"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "supabase",
            "tags": ["database", "postgres", "backend"], "category": "database",
            "homepage": "https://github.com/supabase-community/supabase-mcp",
            "envSchema": [{"key": "SUPABASE_ACCESS_TOKEN", "required": True,
                           "description": "supabase.com 控制台生成的 Access Token"},
                          {"key": "SUPABASE_PROJECT_ID", "required": False,
                           "description": "可选：直连某个项目，避免每次列出"}],
            "notes": "官方 npm 分发，token 走环境变量。",
        },
        {
            "name": "duckdb",
            "description": "DuckDB MCP（MotherDuck 维护）：对本地/内存 DuckDB 跑分析 SQL——单文件 OLAP，CSV/Parquet 直接查询。",
            "transport": "STDIO", "command": "uvx",
            "args": ["mcp-server-duckdb", "--db-path", ":memory:"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "motherduck",
            "tags": ["database", "olap", "analytics"], "category": "database",
            "homepage": "https://github.com/motherduckdb/mcp-server-duckdb",
            "envSchema": [{"key": "motherduck_token", "required": False,
                           "description": "可选：连接 MotherDuck 云端（md: 数据库）"}],
            "notes": "默认内存库；--db-path 可指到 /workspace 持久化文件。",
        },
        {
            "name": "neon",
            "description": "Neon 官方 MCP：serverless Postgres 平台的项目/分支/表管理与时点恢复——分支即数据库的云原生玩法。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@neondatabase/mcp-server-neon"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "neondatabase",
            "tags": ["database", "postgres", "serverless"], "category": "database",
            "homepage": "https://github.com/neondatabase/mcp-server-neon",
            "envSchema": [{"key": "NEON_API_KEY", "required": True,
                           "description": "console.neon.tech 生成的 API Key"}],
            "notes": "官方 npm 分发。",
        },
        {
            "name": "elasticsearch",
            "description": "Elastic 官方 MCP：对 Elasticsearch 集群跑查询/聚合、管理索引与映射——日志与检索场景的直连通道。",
            "transport": "STDIO", "command": "npx",
            "args": ["-y", "@elastic/mcp-server-elasticsearch"],
            "env": {}, "runInSandbox": True, "enabled": False, "scope": "coding",
            "requiresRootfs": True, "vendor": "elastic",
            "tags": ["database", "search", "observability"], "category": "database",
            "homepage": "https://github.com/elastic/mcp-server-elasticsearch",
            "envSchema": [{"key": "ES_URL", "required": False,
                           "description": "集群地址（默认 http://localhost:9200）"},
                          {"key": "ES_API_KEY", "required": False,
                           "description": "可选：Encoded API Key（无则匿名/基础认证）"}],
            "notes": "官方 npm 分发。",
        },
    ]

    # 5) 组装 index
    order = list(CATEGORY_LABELS)
    servers.sort(key=lambda s: (order.index(s["category"]), s["name"]))
    names = [s["name"] for s in servers]
    assert len(names) == len(set(names)) == 50, f"expect 50 unique, got {len(names)}"
    assert all(s.get("transport") in ("STDIO", "HTTP") for s in servers)

    idx = {
        "schema": "apex-mcp-hub-v1",
        "name": "Apex MCP Hub",
        "description": "Apex Agent official MCP server repository — 50 verified servers across 15 categories (sandbox npx/uvx + hosted remote HTTP), installable on demand from the in-app Market.",
        "count": len(servers),
        "categories": {k: {"label": v, "count": 0} for k, v in CATEGORY_LABELS.items()},
        "changelog": [
            {
                "version": "2.0.0",
                "date": "2026-10-03",
                "notes": "v2 重组：并入 Android-Guru-Agent 内置 mcp_catalog 32 台（APK 不再随包分发）；修复 fetch/time 指向不存在 npm 包的问题；新增 microsoft-learn/context7-remote/amap/firecrawl/paper-search/mongodb/supabase/duckdb/neon/elasticsearch 十台（端点与包名逐一经 npm/PyPI/HTTP 握手验证）；全目录按 15 类分类（category 字段，前向兼容）。"
            }
        ],
        "servers": servers,
    }
    for s in servers:
        idx["categories"][s["category"]]["count"] += 1

    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(idx, fp, ensure_ascii=False, indent=2)
        fp.write("\n")

    print(f"OK: {len(servers)} servers, {len(CATEGORY_LABELS)} categories, "
          f"{os.path.getsize(OUT)} bytes")
    for c in order:
        n = idx["categories"][c]["count"]
        if n:
            print(f"  {c} ({CATEGORY_LABELS[c]}): {n}")


if __name__ == "__main__":
    main()
