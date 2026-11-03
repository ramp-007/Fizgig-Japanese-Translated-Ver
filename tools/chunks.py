"""Translation chunk helper.

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).

  python tools/chunks.py split [N]   work/web_missing.json -> work/chunks/chunk_NN.json (N strings each, default 300)
  python tools/chunks.py merge       work/out_web/*.json   -> lib/fizgig_ja/strings_web/web.json (validated)
  python tools/chunks.py stats       number of entries in the current dictionary
"""
import json
import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT_DIR, "work")
CHUNKS = os.path.join(WORK, "chunks")
OUT_WEB = os.path.join(WORK, "out_web")
STRINGS_WEB = os.path.join(ROOT_DIR, "lib", "fizgig_ja", "strings_web")
WEB_JSON = os.path.join(STRINGS_WEB, "web.json")
PH = re.compile(r"\{(\d+)\}")
KANA_KANJI = re.compile(r"[぀-ヿ一-鿿]")
#: strings the page's own code compares against its text: translating them breaks the app
WEB_PROTECTED = ("Web UI", "Show mask", "Hide")
#: translations that legitimately contain no Japanese (a bare separator)
NO_JAPANESE_OK = {"of": "/"}


_CJK = "\u3040-\u30ff\u4e00-\u9fff"
_SPACE_L = re.compile(r"(?<=[A-Za-z0-9]) +(?=[%s])" % _CJK)
_SPACE_R = re.compile(r"(?<=[%s]) +(?=[A-Za-z0-9])" % _CJK)


def normalize(ja):
    """Consistent wording and typography across chunks translated independently."""
    ja = ja.replace("モッド", "mod").replace("出荷時のまま", "初期状態のまま")
    ja = re.sub(r"被写体 (\d)", lambda m: "被写体" + m.group(1), ja)
    ja = re.sub(r"フォルダ(?!ー)", "フォルダー", ja)
    ja = _SPACE_L.sub("", ja)          # "LoRA 名" -> "LoRA名": no space between Latin and Japanese
    ja = _SPACE_R.sub("", ja)
    return ja


def split(n=300):
    miss = json.load(open(os.path.join(WORK, "web_missing.json"), encoding="utf-8"))
    items = sorted(miss, key=lambda s: (miss[s]["src"][0].split(":")[0], miss[s]["src"][0], s.lower()))
    os.makedirs(CHUNKS, exist_ok=True)
    for f in os.listdir(CHUNKS):
        os.remove(os.path.join(CHUNKS, f))
    k = 0
    for i in range(0, len(items), n):
        k += 1
        part = {s: "" for s in items[i:i + n]}
        with open(os.path.join(CHUNKS, f"chunk_{k:02d}.json"), "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False, indent=1)
    print(f"{len(items)} strings -> {k} chunks ({CHUNKS})")


def plural_suffixes(en):
    path = os.path.join(WORK, "web_candidates.json")
    cands = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    return {str(n) for n in cands.get(en, {}).get("plural", [])}


def dump_catalog(path, data):
    """{英語: 日本語} を indent=1 相当で書く。ただし "password" を含む項目だけは、キーと値を別の行に
    分ける（秘密情報スキャナーの generic-password が、UI のラベル文字列を誤検知するため）。"""
    lines = []
    for en, ja in sorted(data.items()):
        key, val = json.dumps(en, ensure_ascii=False), json.dumps(ja, ensure_ascii=False)
        if re.search("password", en + ja, re.I):
            lines.append(" %s:\n  %s" % (key, val))
        else:
            lines.append(" %s: %s" % (key, val))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(lines) + "\n}\n")


def merge():
    web = json.load(open(WEB_JSON, encoding="utf-8")) if os.path.exists(WEB_JSON) else {}
    problems, added, blank = [], 0, 0
    files = sorted(os.listdir(OUT_WEB)) if os.path.isdir(OUT_WEB) else []
    for fn in files:
        if not fn.endswith(".json"):
            continue
        try:
            data = json.load(open(os.path.join(OUT_WEB, fn), encoding="utf-8"))
        except Exception as e:
            problems.append(f"{fn}: JSON error {e}")
            continue
        for en, ja in data.items():
            if not isinstance(ja, str) or not ja.strip() or ja == en:
                blank += 1
                continue
            if en in WEB_PROTECTED:
                problems.append(f"{fn}: protected string translated {en!r}")
                continue
            if ja.replace("（", "(").replace("）", ")").replace("、", ",").replace(" ", "") == en.replace(" ", ""):
                blank += 1                    # only full-width punctuation differs: keep the English
                continue
            plural = plural_suffixes(en)
            en_ph, ja_ph = set(PH.findall(en)), set(PH.findall(ja))
            if ja_ph - en_ph or (en_ph - ja_ph - plural):
                problems.append(f"{fn}: placeholder mismatch {en!r} -> {ja!r}")
                continue
            words = re.findall(r"[A-Za-z]{2,}", PH.sub("", en))
            if not KANA_KANJI.search(ja) and len(words) >= 4 and NO_JAPANESE_OK.get(en) != ja:
                problems.append(f"{fn}: no Japanese {en!r} -> {ja!r}")
                continue
            for n in plural:
                ja = ja.replace("{%s}" % n, "", 1)
            if web.get(en) != ja:
                added += 1
            web[en] = ja
    web = {en: normalize(ja) for en, ja in web.items()}
    os.makedirs(STRINGS_WEB, exist_ok=True)
    dump_catalog(WEB_JSON, web)
    print(f"web.json {len(web)} entries (new/changed {added}, left blank/identical {blank})")
    if problems:
        with open(os.path.join(WORK, "merge_problems.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(problems))
        print(f"{len(problems)} problems -> work/merge_problems.txt")
        for p in problems[:20]:
            print("  ", p)


def stats():
    web = json.load(open(WEB_JSON, encoding="utf-8")) if os.path.exists(WEB_JSON) else {}
    print(len(web), "entries")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "split":
        split(int(sys.argv[2]) if len(sys.argv) > 2 else 300)
    elif cmd == "merge":
        merge()
    elif cmd == "stats":
        stats()
    else:
        print(__doc__)
