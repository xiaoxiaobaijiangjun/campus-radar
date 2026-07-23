#!/usr/bin/env python3
"""Manually add job postings to the tracker.

Three modes:
  1. Interactive:  python3 add_posting.py --state state/seen_postings.json --config config.json
  2. CLI:          python3 add_posting.py --state ... --company "XX" --title "YY" --city "深圳"
  3. Batch import: python3 add_posting.py --state ... --import my_postings.json

Added postings go directly into state/seen_postings.json with source_platform="手动添加"
(unless overridden). They appear in the next Excel export alongside auto-discovered ones.
"""
import argparse
import json
import os
import sys
from datetime import date, datetime

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")

def make_hash(company, title, url):
    import hashlib, re
    def norm(s):
        s = (s or "").strip()
        s = re.sub(r"\s+", "", s)
        return s.lower()
    key = f"{norm(company)}|{norm(title)}|{(url or '').strip()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def add_single(state, company, title, city="未注明", highlight="",
               source_url="", apply_url="", deadline="", source_platform="手动添加"):
    """Add one posting to state. Returns (hash, is_new)."""
    postings = state.setdefault("postings", {})
    h = make_hash(company, title, source_url)

    today = date.today().isoformat()
    if h in postings:
        postings[h]["last_confirmed"] = today
        return h, False

    # Also check fuzzy (same company+title, different URL)
    import re
    def norm(s):
        return re.sub(r"\s+", "", (s or "").strip().lower())
    fkey = f"{norm(company)}|{norm(title)}"
    for existing_h, rec in postings.items():
        if f"{norm(rec.get('company',''))}|{norm(rec.get('title',''))}" == fkey:
            postings[existing_h]["last_confirmed"] = today
            return existing_h, False

    rec = {
        "company": company,
        "title": title,
        "city": city,
        "highlight": highlight,
        "source_platform": source_platform,
        "source_url": source_url,
        "apply_url": apply_url,
        "deadline": deadline,
        "first_seen": today,
        "last_confirmed": today,
    }
    postings[h] = rec
    return h, True

def interactive_add(state, config):
    """Interactive prompt mode."""
    count_new = 0
    count_dup = 0

    print("=" * 50)
    print("  📝 手动添加岗位到追踪表")
    print("  输入 q 退出，留空字段使用默认值")
    print("=" * 50)

    while True:
        print()
        company = input("公司名称: ").strip()
        if company.lower() == "q":
            break
        if not company:
            print("  ⚠️ 公司名称不能为空")
            continue

        title = input("岗位名称: ").strip()
        if title.lower() == "q":
            break
        if not title:
            print("  ⚠️ 岗位名称不能为空")
            continue

        city = input("工作城市 [未注明]: ").strip() or "未注明"
        highlight = input("岗位亮点(可选): ").strip()
        source_url = input("来源链接(可选): ").strip()
        apply_url = input("投递入口(可选): ").strip()
        deadline = input("截止日期(可选, YYYY-MM-DD): ").strip()
        source_platform = input("来源平台 [手动添加]: ").strip() or "手动添加"

        if deadline.lower() == "q":
            break
        if source_url.lower() == "q":
            break

        h, is_new = add_single(state, company, title, city, highlight,
                               source_url, apply_url, deadline, source_platform)

        if is_new:
            print(f"  ✅ 已添加：{company} - {title}")
            count_new += 1
        else:
            print(f"  ⏭️ 已存在，跳过：{company} - {title}")
            count_dup += 1

        cont = input("\n继续添加？(y/n) [y]: ").strip().lower()
        if cont == "n" or cont == "q":
            break

    return count_new, count_dup

def main():
    ap = argparse.ArgumentParser(description="手动添加岗位到追踪表")
    ap.add_argument("--state", required=True, help="Path to seen_postings.json")
    ap.add_argument("--config", required=True, help="Path to config.json")
    ap.add_argument("--company", help="公司名称（CLI模式）")
    ap.add_argument("--title", help="岗位名称（CLI模式）")
    ap.add_argument("--city", default="未注明", help="工作城市")
    ap.add_argument("--highlight", default="", help="岗位亮点")
    ap.add_argument("--source-url", default="", help="来源链接")
    ap.add_argument("--apply-url", default="", help="投递入口")
    ap.add_argument("--deadline", default="", help="截止日期 YYYY-MM-DD")
    ap.add_argument("--source-platform", default="手动添加", help="来源平台")
    ap.add_argument("--import", dest="import_file", help="批量导入 JSON 文件")
    args = ap.parse_args()

    config = load_json(args.config, {})
    state = load_json(args.state, {
        "schema_version": 1,
        "season": config.get("target_season_label", "season"),
        "last_run": None,
        "postings": {}
    })

    # ── Batch import mode ──
    if args.import_file:
        data = load_json(args.import_file, [])
        if not isinstance(data, list):
            print("ERROR: import file must be a JSON array", file=sys.stderr)
            sys.exit(1)
        count_new = 0
        count_dup = 0
        for item in data:
            h, is_new = add_single(state,
                item.get("company", ""),
                item.get("title", ""),
                item.get("city", "未注明"),
                item.get("highlight", ""),
                item.get("source_url", ""),
                item.get("apply_url", ""),
                item.get("deadline", ""),
                item.get("source_platform", "手动添加"))
            if is_new:
                count_new += 1
            else:
                count_dup += 1
        print(f"批量导入完成：新增 {count_new}，重复跳过 {count_dup}")

    # ── CLI single mode ──
    elif args.company and args.title:
        h, is_new = add_single(state, args.company, args.title, args.city,
                               args.highlight, args.source_url, args.apply_url,
                               args.deadline, args.source_platform)
        if is_new:
            print(f"✅ 已添加：{args.company} - {args.title}")
        else:
            print(f"⏭️ 已存在：{args.company} - {args.title}")

    # ── Interactive mode ──
    else:
        count_new, count_dup = interactive_add(state, config)
        print(f"\n本次新增 {count_new} 个岗位，跳过 {count_dup} 个重复")

    # Save state
    state["last_run"] = datetime.now().astimezone().isoformat()
    save_json(args.state, state)

    total = len(state.get("postings", {}))
    print(f"当前共追踪 {total} 个岗位")
    print("提示：运行 export_excel.py 更新 Excel 追踪表")

if __name__ == "__main__":
    main()
