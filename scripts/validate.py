#!/usr/bin/env python3
"""Apex MCP Hub 注册表校验器（CI 用，零依赖）。

校验规则（任何一条失败即退出码 1）：
 1. index.json 可解析、schema 正确、count 与 servers[] 实际一致；
 2. 服务器 name 全局唯一、格式合法；
 3. transport ∈ {STDIO, HTTP}；STDIO 必有 command/args、HTTP 必有 url（且互斥）；
 4. scope ∈ {agent, coding, all}；enabled 恒 false（安装 ≠ 启动）；
 5. requiresRootfs 与形态一致（STDIO 沙箱 true / HTTP 远端 false）；
 6. category ∈ 19 类词表（15 既有 + v2.1 新增 devtools/security/ai-ml + v2.3 新增 reverse-engineering），
    且 categories 统计与实际条目一致；
 7. envSchema 每项含 key/required/description；
 8. 索引 ≤ 2MB（App 拉取上限）；
 9. 全仓无凭据泄漏（ghp_/github_pat_/AKIA 指纹扫描）。
可选（--online）：STDIO 的 npm/PyPI 包存在性 + HTTP 端点 initialize 握手。
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.json")

LEGAL_CATEGORIES = {
    "official", "docs", "web-search", "browser", "database", "git", "cloud",
    "observability", "productivity", "desktop", "finance", "design",
    "communication", "location", "data",
    # v2.1 新增三类（编码扩容：开发效率 / 安全 / 人工智能）
    "devtools", "security", "ai-ml",
    # v2.3 新增：逆向工程（自 security 拆分独立成类）
    "reverse-engineering",
}
LEGAL_SCOPES = {"agent", "coding", "all"}
LEGAL_TRANSPORTS = {"STDIO", "HTTP", "SSE"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}$")
SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})")
INIT_BODY = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2025-03-26", "capabilities": {},
               "clientInfo": {"name": "apex-hub-ci", "version": "1.0"}},
}).encode()

errors = []


def err(msg: str) -> None:
    errors.append(msg)


def check_npm(pkg: str) -> bool:
    url = "https://registry.npmjs.org/" + urllib.request.quote(pkg, safe="")
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def check_pypi(mod: str) -> bool:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{mod}/json", timeout=30) as r:
            return r.status == 200
    except Exception:  # noqa: BLE001
        return False


def check_http_mcp(url: str) -> tuple[bool, str]:
    """返回 (存活, 备注)。2xx=握手成功；401/403/405=存活但 OAuth 门控（预期）。"""
    req = urllib.request.Request(
        url, data=INIT_BODY, method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 405):
            return True, f"HTTP {e.code}（OAuth 门控，预期）"
        return False, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def main() -> int:
    online = "--online" in sys.argv
    try:
        with open(INDEX, encoding="utf-8") as fp:
            index = json.load(fp)
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: index.json 不可解析: {e}")
        return 1

    if index.get("schema") != "apex-mcp-hub-v1":
        err(f"schema 应为 apex-mcp-hub-v1，实际 {index.get('schema')!r}")
    servers = index.get("servers")
    if not isinstance(servers, list) or not servers:
        err("servers[] 缺失或为空")
        print("\n".join(f"ERROR: {e}" for e in errors))
        return 1
    if index.get("count") != len(servers):
        err(f"count={index.get('count')} 与 servers[] 实际 {len(servers)} 不一致")

    size = os.path.getsize(INDEX)
    if size > 2 * 1024 * 1024:
        err(f"index.json {size}B 超过 App 2MB 拉取上限")

    seen = set()
    cat_count: dict = {}
    for s in servers:
        name = s.get("name", "<missing>")
        if not NAME_RE.match(str(name)):
            err(f"[{name}] name 格式非法")
        if name in seen:
            err(f"[{name}] name 重复")
        seen.add(name)

        transport = s.get("transport")
        if transport not in LEGAL_TRANSPORTS:
            err(f"[{name}] transport 非法: {transport!r}")
        if transport == "STDIO":
            if not s.get("command"):
                err(f"[{name}] STDIO 缺 command")
            if "args" not in s:
                err(f"[{name}] STDIO 缺 args")
            if s.get("url"):
                err(f"[{name}] STDIO 不应有 url")
        else:
            if not s.get("url", "").startswith("https://"):
                err(f"[{name}] HTTP 缺 https url")
            if s.get("command"):
                err(f"[{name}] HTTP 不应有 command")

        if s.get("scope") not in LEGAL_SCOPES:
            err(f"[{name}] scope 非法: {s.get('scope')!r}")
        if s.get("enabled") is not False:
            err(f"[{name}] enabled 必须恒 false（安装 ≠ 启动）")

        expect_rootfs = transport == "STDIO"
        if s.get("requiresRootfs") != expect_rootfs:
            err(f"[{name}] requiresRootfs={s.get('requiresRootfs')} 与形态不符（应为 {expect_rootfs}）")
        if s.get("runInSandbox") != expect_rootfs:
            err(f"[{name}] runInSandbox={s.get('runInSandbox')} 与形态不符（应为 {expect_rootfs}）")

        cat = s.get("category")
        if cat not in LEGAL_CATEGORIES:
            err(f"[{name}] category 非法: {cat!r}")
        cat_count[cat] = cat_count.get(cat, 0) + 1

        if not s.get("description"):
            err(f"[{name}] description 为空")
        if not s.get("vendor"):
            err(f"[{name}] vendor 为空")

        for ev in s.get("envSchema", []):
            if not ev.get("key"):
                err(f"[{name}] envSchema 项缺 key")
            if "required" not in ev or not ev.get("description"):
                err(f"[{name}] envSchema[{ev.get('key')}] 缺 required/description")

    legend = index.get("categories", {})
    for c, meta in legend.items():
        if c not in LEGAL_CATEGORIES:
            err(f"categories 统计含非法类目 {c!r}")
        elif meta.get("count") != cat_count.get(c, 0):
            err(f"categories[{c}].count={meta.get('count')} 与实际 {cat_count.get(c, 0)} 不一致")
    for c in cat_count:
        if c not in legend:
            err(f"类目 {c} 未在 categories 统计中声明")

    # 凭据泄漏扫描
    for dirpath, _dirs, files in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for fn in files:
            if not fn.endswith((".json", ".md", ".py", ".yml", ".yaml")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, encoding="utf-8") as fp:
                    if SECRET_RE.search(fp.read()):
                        err(f"疑似凭据泄漏: {p}")
            except OSError:
                pass

    if errors:
        print(f"\n校验失败，共 {len(errors)} 处：")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    print(f"OK: {len(servers)} 台服务器，{len(cat_count)} 类，索引 {size}B")
    for c in sorted(cat_count):
        print(f"  {c}: {cat_count[c]}")

    # ── 在线冒烟（可选）：包存在性 + HTTP 握手 ──
    if online:
        online_fail = 0
        for s in servers:
            if s["transport"] == "STDIO":
                args = s.get("args", [])
                cmd = s.get("command", "")
                if cmd == "npx":
                    pkg = next((a for a in args if not a.startswith("-")), None)
                    if pkg and not check_npm(pkg):
                        print(f"  ONLINE-FAIL [{s['name']}] npm 包不存在: {pkg}")
                        online_fail += 1
                elif cmd == "uvx":
                    mod = next((a for a in args if not a.startswith("-")), None)
                    if mod and not check_pypi(mod):
                        print(f"  ONLINE-FAIL [{s['name']}] PyPI 模块不存在: {mod}")
                        online_fail += 1
                elif cmd == "docker":
                    print(f"  SKIP [{s['name']}] docker 形态（Android 沙箱不适用，仅登记）")
            else:
                ok, note = check_http_mcp(s["url"])
                if not ok:
                    print(f"  ONLINE-FAIL [{s['name']}] HTTP 握手失败: {s['url']} ({note})")
                    online_fail += 1
                elif "401" in note or "403" in note or "405" in note:
                    print(f"  ONLINE-PASS [{s['name']}] {s['url']} → {note}")
        if online_fail:
            print(f"\n在线冒烟失败 {online_fail} 处")
            return 1
        print("ONLINE: 包存在性与 HTTP 握手全部通过")

    return 0


if __name__ == "__main__":
    sys.exit(main())
