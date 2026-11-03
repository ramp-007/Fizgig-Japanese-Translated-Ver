"""Coverage report: how many UI strings were found, translated, kept in English on purpose, or left untranslated.

Reads work/web_candidates.json (made by tools/extract_web.py) and the shipped dictionary, and prints Markdown.

  python tools/report.py
"""
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import extract_web  # noqa: E402
from extract_web import _engine_covered, _keep_english  # noqa: E402

PROTECTED = ("Web UI", "Show mask", "Hide")


def main():
    cands = json.load(open(os.path.join(ROOT_DIR, "work", "web_candidates.json"), encoding="utf-8"))
    web = extract_web._load_dir(extract_web.STRINGS_WEB)
    overrides_path = os.path.join(ROOT_DIR, "lib", "fizgig_ja", "overrides.json")
    overrides = json.load(open(overrides_path, encoding="utf-8")) if os.path.exists(overrides_path) else {}
    keys = list(cands)
    covered = _engine_covered(keys, {**web, **overrides}) | {k for k in keys if (web.get(k) or overrides.get(k)) and k not in PROTECTED}
    keep = _keep_english()
    translated = [k for k in keys if k in covered and k not in PROTECTED]
    kept = [k for k in keys if k not in covered and (k in PROTECTED or keep(k) or keep(extract_web._norm(k)))]
    left = [k for k in keys if k not in covered and k not in kept]
    by_src = {}
    for k in keys:
        src = cands[k]["src"][0].split(":")[0]
        d = by_src.setdefault(src, [0, 0, 0, 0])
        d[0] += 1
        d[1 if k in covered else 2 if k in kept else 3] += 1
    print(f"- target strings found: **{len(keys)}**")
    print(f"- translated: **{len(translated)}**")
    print(f"- kept in English on purpose: **{len(kept)}**")
    print(f"- untranslated: **{len(left)}**")
    print(f"- dictionary entries shipped: **{len(web)}**")
    print()
    print("| source | found | translated | kept English | untranslated |")
    print("|---|---|---|---|---|")
    for src, d in sorted(by_src.items()):
        print(f"| {src} | {d[0]} | {d[1]} | {d[2]} | {d[3]} |")
    if left:
        print()
        print("untranslated:")
        for k in left[:50]:
            print("-", repr(k[:100]))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
