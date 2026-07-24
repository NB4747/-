#!/usr/bin/env python3
"""
夸克网盘 API 工具 v4
自动读取网盘文件列表，按子文件夹生成分享链接，智能分类，更新 resources.json。

用法：
  1. 浏览器登录 pan.quark.cn → F12 → Console → 输入 document.cookie → 复制结果
  2. 粘贴到 cookie.txt
  3. 运行: python scripts/quark_fetch.py
"""

import sys
import json
import time
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = ROOT / "cookie.txt"
DATA_FILE = ROOT / "data" / "resources.json"
API_BASE = "https://drive-pc.quark.cn/1/clouddrive"

MAIN_FOLDER_FID = "08af4d83f26e4c6bb1117714bc9025d2"

CATEGORY_RULES = [
    (["动漫", "番剧", "海贼", "怪兽", "巨人", "鬼灭", "星际牛仔", "EVA", "福音战士",
      "强风吹拂", "动画", "新番", "日漫"],
     "anime", "动漫番剧", "🎬", "热门日漫、动画番剧合集"),
    (["图书", "书籍", "出版社", "绝版", "相命", "全集", "中信", "电子书"],
     "books", "图书资料", "📚", "各类电子书、绝版书籍、出版社合集"),
    (["小吃", "美食", "食谱", "烹饪", "烧腊", "冷艺", "甜点", "面点", "减肥", "减脂"],
     "cooking", "美食烹饪", "🍳", "小吃教程、烹饪技巧、减脂食谱"),
    (["英语", "雅思", "新概念", "单词", "口语", "听力", "语法", "VIP"],
     "education", "学习教育", "🎓", "英语学习、雅思备考、教学课程"),
    (["Excel", "excel", "WPS", "wps", "办公", "PDF", "谷歌", "Google",
      "TTS", "TTSMaker"],
     "tools", "实用工具", "🛠️", "办公软件、效率工具、实用程序"),
    (["纪录片", "BBC", "影视", "拍摄", "摄影", "iPhone", "电影感"],
     "video", "影视教程", "🎥", "纪录片、影视制作、拍摄教程"),
    (["短剧", "变现", "赚钱", "推广", "淘金", "搬运", "日入"],
     "business", "创业变现", "💼", "副业赚钱、短视频变现教程"),
    (["穿搭", "男士", "变帅", "形象", "服装"],
     "fashion", "穿搭形象", "👔", "男士穿搭、形象提升攻略"),
    (["维修", "家电", "彩电", "冰箱", "空调", "洗衣机", "电脑组装", "电路",
      "显示器", "万用表"],
     "repair", "维修技能", "🔧", "家电维修、电脑组装、电子维修"),
    (["漫威", "marvel", "DC", "蝙蝠侠", "超人", "蜘蛛侠", "钢铁侠", "美队",
      "变形金刚", "毒液", "雷神", "漫画"],
     "comics", "漫画资源", "💬", "漫威、DC 漫画合集"),
]

DEFAULT_CATEGORY = ("other", "其他资源", "📦", "其他各类资源")


def load_cookie():
    if not COOKIE_FILE.exists():
        print(f"❌ 找不到 {COOKIE_FILE}")
        sys.exit(1)
    raw = COOKIE_FILE.read_text(encoding="utf-8-sig").strip()
    if not raw:
        print("❌ cookie.txt 为空")
        sys.exit(1)
    return raw


def create_session(cookie_str):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://pan.quark.cn/",
        "Origin": "https://pan.quark.cn",
    })
    s.headers["Cookie"] = cookie_str
    return s


def list_folder(session, fid):
    """列出文件夹内容"""
    items = []
    page_token = None
    while True:
        params = {"pdir_fid": fid, "_size": 200, "_fetch_total": 1, "pr": "ucpro", "fr": "pc"}
        if page_token:
            params["_page_token"] = page_token
        r = session.get(f"{API_BASE}/file/sort", params=params, timeout=30)
        if r.status_code != 200:
            break
        data = r.json()
        lst = data.get("data", {}).get("list", [])
        items.extend(lst)
        page_token = data.get("data", {}).get("next_page_token", "")
        if not page_token or not lst:
            break
    return items


def create_share(session, fid):
    """创建分享链接，返回 https://pan.quark.cn/s/xxx"""
    # Step 1: Create share task
    r = session.post(
        f"{API_BASE}/share",
        json={"fid_list": [fid], "expired_type": 2, "need_password": 0, "url_type": 1},
        params={"pr": "ucpro", "fr": "pc"},
        timeout=30
    )
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("code") != 0:
        return None

    task_id = data["data"]["task_id"]

    # Step 2: Poll for task completion
    for _ in range(10):
        time.sleep(1)
        r = session.get(
            f"{API_BASE}/task",
            params={"task_id": task_id, "pr": "ucpro", "fr": "pc", "retry_index": 0},
            timeout=30
        )
        if r.status_code != 200:
            continue
        result = r.json()
        task_status = result.get("data", {}).get("status", -1)
        if task_status == 2:  # completed
            share_id = result["data"].get("share_id", "")
            if share_id:
                return f"https://pan.quark.cn/s/{share_id}"
            return None
        elif task_status in (-1, 3):  # failed
            return None

    return None


def classify_folder(name):
    """自动归类"""
    best_score = 0
    best_cat = DEFAULT_CATEGORY
    for keywords, cid, cname, icon, desc in CATEGORY_RULES:
        score = sum(1 for kw in keywords if kw.lower() in name.lower())
        if score > best_score:
            best_score = score
            best_cat = (cid, cname, icon, desc)
    return best_cat


def main():
    print("=" * 55)
    print("  夸克网盘资源抓取工具 v4")
    print("=" * 55)

    cookie = load_cookie()
    session = create_session(cookie)

    # 验证
    print("📡 验证连接...")
    r = session.get(
        f"{API_BASE}/file/sort",
        params={"pdir_fid": "0", "_size": 1, "_fetch_total": 1, "pr": "ucpro", "fr": "pc"},
        timeout=15
    )
    if r.status_code != 200:
        print("❌ 连接失败，Cookie 可能已过期。")
        sys.exit(1)
    print("✅ 连接成功\n")

    # 列出子文件夹
    print("📂 读取「网盘资源」文件夹...")
    items = list_folder(session, MAIN_FOLDER_FID)
    folders = [i for i in items if i.get("dir")]
    print(f"   找到 {len(folders)} 个子文件夹\n")

    if not folders:
        print("❌ 没有找到子文件夹")
        return

    # 显示
    print("📋 资源列表：")
    print("-" * 50)
    for i, f in enumerate(folders):
        print(f"  {i+1:2d}. {f.get('file_name', '???')}")
    print("-" * 50)

    # 归类
    print("\n🔍 自动归类...")
    categorized = {}
    for f in folders:
        name = f.get("file_name", "")
        cid, cname, icon, desc = classify_folder(name)
        if cid not in categorized:
            categorized[cid] = {"name": cname, "icon": icon, "desc": desc, "folders": []}
        categorized[cid]["folders"].append(f)

    for cid, cat in categorized.items():
        print(f"  {cat['icon']} {cat['name']}: {len(cat['folders'])} 项")

    # 创建分享链接
    total = len(folders)
    print(f"\n📤 正在创建分享链接 (共 {total} 个，预计 {total*3} 秒)...")
    print("-" * 50)

    output_cats = []
    filled = 0
    idx = 0

    for cid, cat in categorized.items():
        resources = []
        for f in cat["folders"]:
            name = f.get("file_name", "")
            fid = f.get("fid", "")
            idx += 1
            print(f"  [{idx}/{total}] {name[:40]}...", end=" ", flush=True)

            link = create_share(session, fid)
            if link:
                print("✅")
                filled += 1
            else:
                print("❌")
                link = ""

            resources.append({
                "name": name,
                "description": name,
                "tags": [],
                "quark_link": link,
            })

        output_cats.append({
            "id": cid,
            "name": cat["name"],
            "icon": cat["icon"],
            "description": cat["desc"],
            "resources": resources,
        })

    # 保存
    output = {
        "site": {
            "title": "网盘资源分享",
            "subtitle": "夸克网盘精选资源合集",
            "description": "涵盖动漫、图书、教程、工具、美食等各类资源"
        },
        "categories": output_cats
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已保存 data/resources.json")
    print(f"   分类: {len(output_cats)} | 资源: {total} | 分享链接: {filled}/{total}")

    # 生成站点
    print("\n🔨 重新生成站点...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py")], cwd=str(ROOT))


if __name__ == "__main__":
    main()
