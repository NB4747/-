#!/usr/bin/env python3
"""
夸克网盘资源分享 - 静态站点生成器
读取 data/resources.json，生成 GitHub Pages 静态站点。
"""

import sys
import json
import os
import shutil
from pathlib import Path

# Fix Unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "resources.json"
OUTPUT_DIR = ROOT / "docs"
ASSETS_DIR = ROOT / "assets"


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_css():
    return """\
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #f8f9fb;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #5a5f72;
  --border: #e8ecf1;
  --accent: #4f6ef7;
  --accent-hover: #3b54d4;
  --tag-bg: #eef1ff;
  --tag-text: #4f6ef7;
  --sidebar-bg: #ffffff;
  --sidebar-width: 260px;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-hover: 0 4px 16px rgba(0,0,0,.08);
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1117;
    --card-bg: #1a1d27;
    --text: #e4e6ed;
    --text-secondary: #9699ab;
    --border: #2a2d3a;
    --accent: #6c8cff;
    --accent-hover: #8ba3ff;
    --tag-bg: #1e2340;
    --tag-text: #8ba3ff;
    --sidebar-bg: #141620;
    --shadow: 0 1px 3px rgba(0,0,0,.2);
    --shadow-hover: 0 4px 20px rgba(0,0,0,.3);
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  padding: 24px 20px;
  overflow-y: auto;
  z-index: 10;
}

.sidebar-header { margin-bottom: 28px; }
.sidebar-header h1 { font-size: 20px; font-weight: 700; color: var(--text); }
.sidebar-header p { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.search-box {
  width: 100%; padding: 9px 14px;
  border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--bg); color: var(--text);
  font-size: 13px; outline: none; margin-bottom: 20px;
  transition: border-color .2s;
}
.search-box:focus { border-color: var(--accent); }
.search-box::placeholder { color: var(--text-secondary); }

.nav-list { list-style: none; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 6px;
  cursor: pointer; font-size: 14px; color: var(--text-secondary);
  transition: all .15s; margin-bottom: 2px;
  border: none; background: none; width: 100%; text-align: left;
  font-family: inherit;
}
.nav-item:hover { background: var(--bg); color: var(--text); }
.nav-item.active { background: var(--tag-bg); color: var(--accent); font-weight: 600; }
.nav-item .icon { font-size: 18px; flex-shrink: 0; }
.nav-item .count { margin-left: auto; font-size: 12px; opacity: .6; }

.results-info {
  font-size: 12px; color: var(--text-secondary);
  margin: 8px 0 12px 12px; display: none;
}

/* Main */
.main {
  margin-left: var(--sidebar-width);
  flex: 1; padding: 32px 36px;
  max-width: 1100px;
}

.category-section { margin-bottom: 40px; }
.category-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.category-header h2 { font-size: 22px; font-weight: 700; }
.category-header .icon { font-size: 26px; }
.category-desc { color: var(--text-secondary); font-size: 14px; margin-bottom: 16px; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow);
  transition: box-shadow .2s, transform .2s;
}
.card:hover { box-shadow: var(--shadow-hover); transform: translateY(-1px); }
.card h3 { font-size: 15px; font-weight: 600; margin-bottom: 6px; color: var(--text); }
.card p { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5; }

.card-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }

.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag {
  font-size: 11px; padding: 3px 9px; border-radius: 4px;
  background: var(--tag-bg); color: var(--tag-text);
  white-space: nowrap;
}

.card-link {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 13px; color: var(--accent); text-decoration: none;
  font-weight: 500; transition: color .15s;
}
.card-link:hover { color: var(--accent-hover); }
.card-link.no-link { color: var(--text-secondary); opacity: .5; pointer-events: none; }

.empty-state {
  text-align: center; padding: 60px 20px; color: var(--text-secondary);
}
.empty-state .icon { font-size: 48px; margin-bottom: 12px; }
.empty-state p { font-size: 14px; }

/* Mobile toggle */
.menu-toggle {
  display: none; position: fixed; top: 16px; left: 16px; z-index: 20;
  width: 40px; height: 40px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--card-bg);
  color: var(--text); font-size: 20px; cursor: pointer; align-items: center;
  justify-content: center; box-shadow: var(--shadow);
}

.overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 9; }

@media (max-width: 768px) {
  .menu-toggle { display: flex; }
  .sidebar {
    transform: translateX(-100%);
    transition: transform .25s ease;
    box-shadow: 2px 0 16px rgba(0,0,0,.15);
  }
  .sidebar.open { transform: translateX(0); }
  .overlay.show { display: block; }
  .main { margin-left: 0; padding: 20px 16px 20px 56px; }
  .grid { grid-template-columns: 1fr; }
  .category-header h2 { font-size: 18px; }
}

@media (max-width: 480px) {
  .main { padding: 16px 12px 16px 44px; }
  .card { padding: 14px 16px; }
}
"""


def build_js(data):
    categories_json = json.dumps(data["categories"], ensure_ascii=False)
    return f"""\
const categories = {categories_json};

let activeCategory = 'all';
let searchQuery = '';

function renderAll() {{
  const filtered = categories.filter(c => {{
    if (activeCategory !== 'all' && c.id !== activeCategory) return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.resources.some(r =>
        r.name.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.tags.some(t => t.toLowerCase().includes(q))
      )
    );
  }});

  const main = document.getElementById('content');
  const count = filtered.reduce((sum, c) => sum + c.resources.length, 0);

  if (filtered.length === 0) {{
    main.innerHTML = `<div class="empty-state">
      <div class="icon">🔍</div>
      <p>没有找到匹配的资源，换个关键词试试</p>
    </div>`;
  }} else {{
    let html = '';
    filtered.forEach(cat => {{
      html += `<section class="category-section" id="cat-${{cat.id}}">
        <div class="category-header"><span class="icon">${{cat.icon}}</span><h2>${{cat.name}}</h2></div>
        <p class="category-desc">${{cat.description}}</p>
        <div class="grid">`;
      cat.resources.forEach(r => {{
        const hasLink = r.quark_link && r.quark_link.trim();
        html += `<div class="card">
          <h3>${{r.name}}</h3>
          <p>${{r.description}}</p>
          <div class="card-footer">
            <div class="tags">${{r.tags.map(t => `<span class="tag">${{t}}</span>`).join('')}}</div>
            <a class="card-link${{hasLink ? '' : ' no-link'}}" href="${{hasLink ? r.quark_link : '#'}}"
               target="_blank" rel="noopener" ${{hasLink ? '' : 'onclick="return false"'}}>
              ${{hasLink ? '前往下载 &#8599;' : '待补充'}}
            </a>
          </div>
        </div>`;
      }});
      html += '</div></section>';
    }});
    main.innerHTML = html;
  }}

  // Update results info
  document.getElementById('results-info').style.display = searchQuery ? 'block' : 'none';
  document.getElementById('results-info').textContent = `找到 ${{count}} 个资源`;
}}

function updateNav() {{
  document.querySelectorAll('.nav-item').forEach(el => {{
    el.classList.toggle('active', el.dataset.cat === activeCategory);
  }});
}}

function setCategory(catId) {{
  activeCategory = catId;
  updateNav();
  renderAll();
  // Close sidebar on mobile
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('overlay').classList.remove('show');
}}

function handleSearch(e) {{
  searchQuery = e.target.value.trim();
  renderAll();
}}

// Init
document.addEventListener('DOMContentLoaded', () => {{
  renderAll();

  document.getElementById('menu-toggle').addEventListener('click', () => {{
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('overlay').classList.toggle('show');
  }});

  document.getElementById('overlay').addEventListener('click', () => {{
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('overlay').classList.remove('show');
  }});
}});
"""


def build_html(data):
    nav_items = "\n".join(
        f'<button class="nav-item" data-cat="{cat["id"]}" onclick="setCategory(\'{cat["id"]}\')">'
        f'<span class="icon">{cat["icon"]}</span>{cat["name"]}'
        f'<span class="count">{len(cat["resources"])}</span></button>'
        for cat in data["categories"]
    )
    site = data["site"]
    css = build_css()
    js = build_js(data)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{site["title"]}</title>
<meta name="description" content="{site["description"]}">
<style>{css}</style>
</head>
<body>

<button class="menu-toggle" id="menu-toggle" aria-label="菜单">&#9776;</button>
<div class="overlay" id="overlay"></div>

<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h1>{site["title"]}</h1>
    <p>{site["subtitle"]}</p>
  </div>
  <input type="text" class="search-box" placeholder="搜索资源..."
         oninput="handleSearch(event)" aria-label="搜索">
  <nav>
    <ul class="nav-list">
      <li><button class="nav-item active" data-cat="all" onclick="setCategory('all')">
        <span class="icon">🏠</span>全部资源
      </button></li>
      {nav_items}
    </ul>
    <div class="results-info" id="results-info"></div>
  </nav>
  <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
              font-size: 11px; color: var(--text-secondary); line-height: 1.8;">
    <p>资源来自夸克网盘</p>
    <p>点击「前往下载」获取</p>
    <p>链接失效请联系更新</p>
  </div>
</aside>

<main class="main" id="content"></main>

<script>{js}</script>
</body>
</html>"""


def build_site():
    data = load_data()

    # Ensure output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Generate index.html
    html = build_html(data)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    # Copy assets if any
    if ASSETS_DIR.exists() and any(ASSETS_DIR.iterdir()):
        shutil.copytree(ASSETS_DIR, OUTPUT_DIR / "assets", dirs_exist_ok=True)

    # Generate CNAME if exists
    cname_file = ROOT / "CNAME"
    if cname_file.exists():
        shutil.copy(cname_file, OUTPUT_DIR / "CNAME")

    total = sum(len(cat["resources"]) for cat in data["categories"])
    no_link = sum(
        1 for cat in data["categories"]
        for r in cat["resources"] if not r.get("quark_link", "").strip()
    )

    print(f"✅ 站点生成完成！")
    print(f"   输出目录: {OUTPUT_DIR}")
    print(f"   分类数: {len(data['categories'])}")
    print(f"   资源总数: {total}")
    if no_link:
        print(f"   ⚠️  有 {no_link} 个资源尚未填写夸克分享链接")
    else:
        print(f"   🎉 所有资源均已填写链接")


if __name__ == "__main__":
    build_site()
