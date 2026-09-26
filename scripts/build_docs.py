#!/usr/bin/env python3
"""把仓库里的原始 Markdown 组装成 MkDocs 的源目录 build/docs。

站点正文逐字取自仓库中的原始文件，不做任何改写：

- mkdocs.yml 的 nav 中登记的页面 → 按原路径复制到 build/docs
- README.md → build/docs/index.md，并在末尾追加一节可点击的站内目录
- assets/ → build/docs/assets/

同时做两项完整性校验，任何一项不通过就直接失败：

1. nav 里登记的每个页面都必须真实存在；
2. 仓库中除白名单外的每个 .md 都必须已登记在 nav 里（防止新增文档漏发布）。

work/（本地语料工作区）、*.epub（电子书原文件）以及 AGENTS.md、SITE.md
这类非正文文件既不复制也不发布。
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "mkdocs.yml"
DOCS_DIR = ROOT / "build" / "docs"
HOME_SOURCE = ROOT / "README.md"

# 不参与站点发布的仓库内容（仍在仓库中保留）
UNPUBLISHED_DIRS = {".git", ".github", ".venv", "__pycache__", "assets", "build", "scripts", "work"}
UNPUBLISHED_FILES = {"AGENTS.md", "SITE.md"}

INDEX_TITLE = "附：站内目录（可点击直达）"


class ConfigLoader(yaml.SafeLoader):
    """mkdocs.yml 里的 !!python/name:、!!python/object/apply: 等扩展标签对本站无可解析语义，
    解析 nav 时按占位值处理。"""


ConfigLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/", lambda loader, suffix, node: None
)


def load_nav() -> list:
    config = yaml.load(CONFIG_FILE.read_text(encoding="utf-8"), Loader=ConfigLoader)
    nav = config.get("nav")
    if not nav:
        sys.exit("mkdocs.yml 缺少 nav 配置")
    return nav


def collect_pages(node, pages: list[str]) -> None:
    """深度优先收集 nav 中的所有页面路径。"""
    if isinstance(node, dict):
        for value in node.values():
            collect_pages(value, pages)
    elif isinstance(node, list):
        for item in node:
            collect_pages(item, pages)
    elif isinstance(node, str):
        pages.append(node)
    else:
        sys.exit(f"nav 中出现无法识别的条目：{node!r}")


def repository_docs() -> list[Path]:
    """仓库中所有应当纳入站点的 Markdown 文件（相对路径）。"""
    found = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if any(part in UNPUBLISHED_DIRS for part in rel.parts):
            continue
        found.append(rel)
    return found


def check_coverage(pages: list[str]) -> None:
    registered = set(pages)
    # index.md 由本脚本从 README.md 生成，不对应仓库中的同名文件
    missing = [p for p in pages if p != "index.md" and not (ROOT / p).is_file()]
    if missing:
        sys.exit("nav 中登记的页面不存在：\n  " + "\n  ".join(missing))
    if not HOME_SOURCE.is_file():
        sys.exit("缺少首页来源 README.md")

    home_rel = str(HOME_SOURCE.relative_to(ROOT))
    unregistered = [
        str(rel)
        for rel in repository_docs()
        if str(rel) not in registered and str(rel) != home_rel and rel.name not in UNPUBLISHED_FILES
    ]
    if unregistered:
        sys.exit("以下 Markdown 既未登记进 nav、也不在排除名单内，请补齐 mkdocs.yml 或明确排除：\n  " + "\n  ".join(unregistered))


def render_index(nav: list) -> str:
    """根据 nav 生成可点击的站内目录。"""
    lines = [f"## {INDEX_TITLE}", ""]

    def walk(node) -> None:
        if isinstance(node, dict):
            for title, value in node.items():
                if isinstance(value, str):
                    if value != "index.md":
                        lines.append(f"- [{title}]({value})")
                else:
                    lines.extend(["", f"### {title}", ""])
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(nav)
    return "\n".join(lines) + "\n"


def main() -> None:
    nav = load_nav()
    pages: list[str] = []
    collect_pages(nav, pages)

    duplicates = {p for p in pages if pages.count(p) > 1}
    if duplicates:
        sys.exit("nav 中重复登记：" + "、".join(sorted(duplicates)))

    check_coverage(pages)

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)

    # 正文目录（nav 中出现的所有顶层目录）原样复制
    for name in sorted({Path(p).parts[0] for p in pages if len(Path(p).parts) > 1}):
        shutil.copytree(ROOT / name, DOCS_DIR / name)

    # 站点资源
    shutil.copytree(ROOT / "assets", DOCS_DIR / "assets")

    # 首页 = README 原文 + 可点击目录
    home = HOME_SOURCE.read_text(encoding="utf-8").rstrip("\n")
    (DOCS_DIR / "index.md").write_text(f"{home}\n\n---\n\n{render_index(nav)}", encoding="utf-8")

    published = len(pages) - 1  # index.md 对应 README
    print(f"build/docs 组装完成：{published} 个页面 + 首页")


if __name__ == "__main__":
    main()
