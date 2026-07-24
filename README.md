# 网盘资源分享

夸克网盘精选资源合集，按分类整理，持续更新。

## 如何使用

### 1. 添加资源

编辑 `data/resources.json`，在对应分类下添加资源：

```json
{
  "name": "资源名称",
  "description": "资源描述",
  "tags": ["标签1", "标签2"],
  "quark_link": "https://pan.quark.cn/s/xxxxx"
}
```

每个资源需要填写夸克网盘的**分享链接**（在夸克中选择文件 → 分享 → 复制链接）。

### 2. 本地预览

```bash
python scripts/generate.py
# 然后打开 docs/index.html 即可预览
```

### 3. 发布

推送到 GitHub `main` 分支即可自动部署到 GitHub Pages。

```bash
git add -A
git commit -m "更新资源"
git push origin main
```

## 项目结构

```
├── data/
│   └── resources.json     # 资源数据（分类 + 资源）
├── scripts/
│   └── generate.py        # 静态站点生成器
├── docs/                  # 生成的站点（GitHub Pages 源）
├── .github/workflows/     # CI/CD 自动部署
└── README.md
```

## 本地环境

- Python 3.8+
- 无需安装额外依赖
