#!/usr/bin/env python3
"""
夸克网盘资源抓取工具 v5 - 基于 QuarkPan 库
自动读取网盘文件列表、批量创建分享链接、智能分类、更新站点。

依赖：QuarkPan 库 (E:\微信公众号工具\QuarkPan)
"""

import sys
import json
import time
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Add QuarkPan library to path
QUARKPAN_PATH = r"E:\微信公众号工具\QuarkPan"
sys.path.insert(0, QUARKPAN_PATH)

try:
    from quark_client.services.share_service import ShareService
    from quark_client.core.api_client import QuarkAPIClient
    from quark_client.services.file_service import FileService
except ImportError as e:
    print(f"❌ 无法导入 QuarkPan 库: {e}")
    print(f"   请确认路径: {QUARKPAN_PATH}")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = ROOT / "cookie.txt"
DATA_FILE = ROOT / "data" / "resources.json"

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
    return COOKIE_FILE.read_text(encoding="utf-8-sig").strip()


def classify_folder(name):
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
    print("  夸克网盘资源抓取工具 v5 (QuarkPan)")
    print("=" * 55)

    cookie = load_cookie()
    client = QuarkAPIClient(cookies=cookie, auto_login=False)
    share_svc = ShareService(client)
    file_svc = FileService(client)

    # 验证连接
    print("📡 验证连接...")
    try:
        root = file_svc.list_files(folder_id="0", size=1)
        if root.get("status") != 200:
            print("❌ 连接失败，Cookie 可能已过期")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        sys.exit(1)
    print("✅ 连接成功\n")

    # 列出子文件夹
    print("📂 读取「网盘资源」文件夹...")
    resp = file_svc.list_files(folder_id=MAIN_FOLDER_FID, size=200)
    items = resp.get("data", {}).get("list", [])
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

    # 批量创建分享
    total = len(folders)
    print(f"\n📤 正在创建分享链接 (共 {total} 个，约需 {total * 3} 秒)...")
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

            try:
                result = share_svc.create_share(
                    file_ids=[fid],
                    title=name,
                    expire_days=0  # 永久
                )
                share_url = result.get("share_url", "")
                if share_url:
                    print("✅")
                    filled += 1
                    time.sleep(1.5)
                else:
                    print("❌ 无URL")
                    share_url = ""
            except Exception as e:
                print(f"❌ {str(e)[:30]}")
                share_url = ""

            resources.append({
                "name": name,
                "description": name,
                "tags": [],
                "quark_link": share_url,
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
