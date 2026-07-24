#!/usr/bin/env python3
"""从 share_links.txt 读取手动填写的分享链接，更新 resources.json 并重新生成站点。

夸克网页端复制分享文案后，直接整段粘贴到资源名后面的 = 右边即可（支持多行）。
"""
import sys, json, re, subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
LINKS_FILE = ROOT / "share_links.txt"
DATA_FILE = ROOT / "data" / "resources.json"


def parse_links():
    if not LINKS_FILE.exists():
        print(f"❌ 找不到 {LINKS_FILE}")
        sys.exit(1)

    text = LINKS_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()

    name_to_url = {}
    name_to_pwd = {}
    current_name = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            before_eq, _, after_eq = line.partition("=")
            before_eq = before_eq.strip()
            after_eq = after_eq.strip()

            # Skip metadata lines (链接/提取码 on left side)
            if "链接" in before_eq or "提取码" in before_eq:
                continue

            # Check if URL is embedded in after_eq
            url_match = re.search(r"https://pan\.quark\.cn/s/\S+", after_eq)
            if url_match:
                name_to_url[before_eq] = url_match.group(0)
                current_name = None
            else:
                current_name = before_eq

        elif current_name:
            if "链接" in line:
                url_match = re.search(r"https://pan\.quark\.cn/s/\S+", line)
                if url_match:
                    name_to_url[current_name] = url_match.group(0)
            if "提取码" in line:
                pwd_match = re.search(r"提取码[：:]\s*(\S+)", line)
                if pwd_match:
                    name_to_pwd[current_name] = pwd_match.group(1)
                    current_name = None

    return name_to_url, name_to_pwd


def main():
    name_to_url, name_to_pwd = parse_links()
    print(f"📋 读取到 {len(name_to_url)} 条分享链接\n")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for cat in data["categories"]:
        for r in cat["resources"]:
            name = r["name"]
            if name in name_to_url:
                r["quark_link"] = name_to_url[name]
                pwd = name_to_pwd.get(name, "")
                if pwd:
                    r["description"] = f"{name} | 提取码: {pwd}"
                updated += 1
                print(f"  ✅ {name[:35]}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(c["resources"]) for c in data["categories"])
    missing = total - updated
    print(f"\n📊 已更新: {updated}/{total}" + (f"  缺 {missing} 个" if missing else "  🎉 全部完成"))

    print("\n🔨 重新生成站点...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py")], cwd=str(ROOT))


if __name__ == "__main__":
    main()
