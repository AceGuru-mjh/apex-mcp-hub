#!/usr/bin/env python3
"""apex-mcp-hub 注册表重算与完整性工具（v2.1 起自包含，不再依赖 ../Android-Guru-Agent 的 mcp_catalog——该目录已随 APK 资产归零而退役）。

用法：
  python3 scripts/build_index.py           # 重算 categories 统计与顶层 count、按（类目,name）排序后原地重写 index.json
  python3 scripts/build_index.py --check   # 只校验不写盘（出错退出码 1，适合本地预检）

与 scripts/validate.py 的分工：validate.py 是 CI 红线校验器（只报错不修）；本工具可
「自愈」统计数字与排序，并额外校验富化字段（description/tags/homepage）的收录质量。

校验规则（--check 下前 7 条任何一条失败即退出码 1；第 8 条为收录质量预警，只提示不拦截——
 v2.1 前的存量条目描述较短属正常，新条目按 80-160 字 / tags 3-6 收录）：
 1. index.json 可解析、schema 为 apex-mcp-hub-v1；
 2. categories 词表 = 18 类（15 既有 + devtools/security/ai-ml），每类 label 非空，
    统计 count 与 servers[] 实际分布一致，顶层 count = len(servers)；
 3. name 全局唯一、格式 ^[a-z0-9][a-z0-9-]{1,48}$；
 4. transport ∈ {STDIO, HTTP, SSE}；STDIO 必有 command/args 且无 url；HTTP 必有 https url 且无 command；
 5. enabled 恒 false（安装 ≠ 启动）；runInSandbox / requiresRootfs 与形态一致（STDIO true / HTTP false）；
    scope ∈ {agent, coding, all}；envSchema 每项含 key / required / description；
 6. 收录质量：description 非空且 ≤ 220、vendor 非空、tags ≥ 1、homepage 为 https；
 7. 索引 ≤ 2MB（App 拉取上限）；
 8. （预警）description < 60 字或 tags < 3 个 → 建议新条目按 v2.1 质量标准补齐。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.json")

# 18 类词表：15 既有 + v2.1 新增三类（顺序即目录呈现顺序）
CATEGORY_ORDER = [
    "official", "docs", "web-search", "browser", "database", "git", "cloud",
    "observability", "productivity", "desktop", "finance", "design",
    "communication", "location", "data", "devtools", "security", "ai-ml",
]
LEGAL_CATEGORIES = set(CATEGORY_ORDER)
LEGAL_SCOPES = {"agent", "coding", "all"}
LEGAL_TRANSPORTS = {"STDIO", "HTTP", "SSE"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}$")

errors = []
warnings = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def validate_and_recompute(idx: dict) -> dict:
    """校验 + 重算统计。返回处理后的 idx（stat 字段已重算、servers 已排序）。"""
    if idx.get("schema") != "apex-mcp-hub-v1":
        err(f"schema 应为 apex-mcp-hub-v1，实际 {idx.get('schema')!r}")

    servers = idx.get("servers")
    if not isinstance(servers, list) or not servers:
        err("servers[] 缺失或为空")
        return idx

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
        elif transport:
            if not str(s.get("url", "")).startswith("https://"):
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
        else:
            cat_count[cat] = cat_count.get(cat, 0) + 1

        # 收录质量（v2.1 起）：硬性=字段存在且非空；软性=长度/标签数为预警
        desc = s.get("description") or ""
        if not (1 <= len(desc) <= 220):
            err(f"[{name}] description 缺失或超过 220 字符")
        elif len(desc) < 60:
            warn(f"[{name}] description 仅 {len(desc)} 字（v2.1 新条目标准为 80-160 字）")
        if not s.get("vendor"):
            err(f"[{name}] vendor 为空")
        tags = s.get("tags") or []
        if len(tags) < 1:
            err(f"[{name}] tags 缺失")
        elif len(tags) < 3:
            warn(f"[{name}] tags 仅 {len(tags)} 个（v2.1 新条目标准为 3-6 个）")
        home = s.get("homepage") or ""
        if not home.startswith("https://"):
            err(f"[{name}] homepage 缺失或非 https: {home!r}")

        for ev in s.get("envSchema", []):
            if not ev.get("key"):
                err(f"[{name}] envSchema 项缺 key")
            if "required" not in ev or not ev.get("description"):
                err(f"[{name}] envSchema[{ev.get('key')}] 缺 required/description")

    # categories 词表与统计勾稽
    legend = idx.get("categories", {})
    for c in CATEGORY_ORDER:
        if c not in legend:
            err(f"categories 统计缺类目 {c!r}")
        elif not legend[c].get("label"):
            err(f"categories[{c}] 缺中文 label")
    for c in legend:
        if c not in LEGAL_CATEGORIES:
            err(f"categories 统计含非法类目 {c!r}")
    # 重算（自愈）
    labels = {c: legend.get(c, {}).get("label", "") for c in CATEGORY_ORDER}
    idx["categories"] = {c: {"label": labels[c], "count": cat_count.get(c, 0)} for c in CATEGORY_ORDER}
    idx["count"] = len(servers)

    # 稳定排序：（类目顺序, name）
    servers.sort(key=lambda s: (CATEGORY_ORDER.index(s.get("category", "zzz")), s.get("name", "")))
    idx["servers"] = servers
    return idx


def main() -> int:
    check_only = "--check" in sys.argv
    if not os.path.exists(INDEX):
        print(f"FATAL: {INDEX} 不存在")
        return 1
    try:
        with open(INDEX, encoding="utf-8") as fp:
            idx = json.load(fp)
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: index.json 不可解析: {e}")
        return 1

    idx = validate_and_recompute(idx)

    size = os.path.getsize(INDEX)
    if size > 2 * 1024 * 1024:
        err(f"index.json {size}B 超过 App 2MB 拉取上限")

    if errors:
        print(f"校验失败，共 {len(errors)} 处：")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    if warnings:
        print(f"质量预警 {len(warnings)} 处（存量条目描述较短属正常，不拦截）：")
        for w in warnings[:10]:
            print(f"  WARN: {w}")
        if len(warnings) > 10:
            print(f"  …另有 {len(warnings) - 10} 处")

    if check_only:
        print(f"OK (check-only): {idx['count']} 台服务器，{len(idx['categories'])} 类，索引 {size}B，无需修复")
        return 0

    with open(INDEX, "w", encoding="utf-8") as fp:
        json.dump(idx, fp, ensure_ascii=False, indent=2)
        fp.write("\n")
    new_size = os.path.getsize(INDEX)
    print(f"OK: 重算完成并重写 index.json —— {idx['count']} 台服务器，{len(idx['categories'])} 类，"
          f"{size}B → {new_size}B")
    for c in CATEGORY_ORDER:
        n = idx["categories"][c]["count"]
        if n:
            print(f"  {c} ({idx['categories'][c]['label']}): {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
