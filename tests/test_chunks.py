"""tools/chunks.py: wording normalisation and merge validation."""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import chunks  # noqa: E402


def test_normalize_removes_space_between_latin_and_japanese():
    assert chunks.normalize("LoRA 名:") == "LoRA名:"
    assert chunks.normalize("Pod を削除") == "Podを削除"
    assert chunks.normalize("{0} 枚") == "{0} 枚"          # placeholders are left alone


def test_normalize_unifies_terms():
    assert chunks.normalize("被写体 1:") == "被写体1:"
    assert chunks.normalize("その他のフォルダ") == "その他のフォルダー"
    assert chunks.normalize("フォルダー") == "フォルダー"
    assert chunks.normalize("LoRA + モッド") == "LoRA + mod"


def _merge_with(data):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "out"))
        with open(os.path.join(d, "out", "c.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        saved = (chunks.OUT_WEB, chunks.STRINGS_WEB, chunks.WEB_JSON, chunks.WORK)
        chunks.OUT_WEB = os.path.join(d, "out")
        chunks.STRINGS_WEB = os.path.join(d, "sw")
        chunks.WEB_JSON = os.path.join(d, "sw", "web.json")
        chunks.WORK = d
        try:
            chunks.merge()
            path = chunks.WEB_JSON
            return json.load(open(path, encoding="utf-8"))
        finally:
            chunks.OUT_WEB, chunks.STRINGS_WEB, chunks.WEB_JSON, chunks.WORK = saved


def test_merge_accepts_good_and_rejects_bad_entries():
    web = _merge_with({
        "Start Training": "学習を開始",
        "Saved {0}": "保存しました: {0}",
        "Lost {0} here": "ここで失われました",              # placeholder dropped
        "Web UI": "ウェブUI",                                 # protected
        "Show mask": "マスクを表示",                          # protected
        "Please wait while the model loads now": "Please wait while the model loads now",  # not translated
        "Skipped": "",
    })
    assert web == {"Start Training": "学習を開始", "Saved {0}": "保存しました: {0}"}
