# 站点构建与部署

在线地址：<https://deng-shihao.github.io/grammar-rl/>

站点用 MkDocs + Material 生成。正文不是副本，而是**逐字取自仓库里的原始 Markdown**：
`scripts/build_docs.py` 按 `mkdocs.yml` 的 `nav` 把原始文件复制进 `build/docs`，
`README.md` 作为首页（末尾自动追加一节可点击的站内目录），`assets/reading.css` 提供阅读样式。

## 本地预览

```bash
uv venv .venv && uv pip install -r requirements.txt   # 首次准备
python3 scripts/build_docs.py                         # 组装 build/docs
mkdocs serve                                          # 打开 http://127.0.0.1:8000
```

改完正文或 `nav` 后重新执行 `python3 scripts/build_docs.py`（`mkdocs serve` 不会自动重跑）。

## 构建产物

```bash
python3 scripts/build_docs.py && mkdocs build --strict
# 输出目录：build/site
```

## 发布

推送到 `main` 后由 `.github/workflows/deploy.yml` 自动构建并发布到 GitHub Pages
（Pages 源设置为 **GitHub Actions**）。也可在 Actions 页面手动触发 `workflow_dispatch`。

## 收录规则

- **发布**：`大纲/`、`真题/`、`知识点-词汇语法/`、`练习/`、`research/` 下的全部 Markdown；
  `README.md` 作为首页。
- **不发布**：`work/`（本地语料工作区，可由 EPUB 重建）、`*.epub`（电子书原文件）、
  `AGENTS.md`、`SITE.md`、`scripts/`、`assets/`（仅作为站点静态资源）、`build/`（构建产物）。
- 新增文档后必须登记进 `mkdocs.yml` 的 `nav`，否则 `scripts/build_docs.py` 会直接报错退出。
