"""Fizgig 8+ Web UI の日本語化。

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).

Fizgig 8 以降のメインアプリは、ローカルサーバー (fizgig.web.server) が返す Web ページです。
サーバーがメインページを返す瞬間に、翻訳スクリプト (web_ja.js) と辞書をページの末尾へ差し込み、
ブラウザ側で画面の文言を日本語に置き換えます。Fizgig のファイルは 1 文字も変更しません。

  - フック箇所: fizgig.web.server.Handler._send（200 / text/html / メインページの目印がある場合だけ）
  - 辞書: strings_web/*.json の後に overrides.json（利用者の上書き）を読む
  - 失敗してもアプリはそのまま動きます（英語のままになるだけ）。エラーは ja_error.log にだけ書きます。
"""
import json
import os
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(_HERE))
WEB_STRINGS_DIR = os.path.join(_HERE, "strings_web")
OVERRIDES = os.path.join(_HERE, "overrides.json")
JS_PATH = os.path.join(_HERE, "web_ja.js")

#: アプリ本体のページだけがこの目印を持つ（他の text/html は報告書やギャラリー）
PAGE_MARK = b'name="fizgig-token"'

#: ページのコードが画面の文字と比較する文言。翻訳すると機能が壊れるので英語のままにする。
#: "Web UI" は環境設定のカードを見つけるタイトル、"Show mask" / "Hide" はボタンの状態判定に使われる。
PROTECTED = ("Web UI", "Show mask", "Hide")

_tag = None


def log_error(where):
    try:
        with open(os.path.join(BASE_DIR, "ja_error.log"), "a", encoding="utf-8") as f:
            f.write(f"--- {where}\n{traceback.format_exc()}\n")
    except Exception:
        pass


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_catalog():
    """{英語: 日本語}。strings_web/*.json を読み、最後に利用者の overrides.json で上書きする。"""
    merged = {}
    if os.path.isdir(WEB_STRINGS_DIR):
        for name in sorted(os.listdir(WEB_STRINGS_DIR)):
            if name.lower().endswith(".json"):
                merged.update(_load_json(os.path.join(WEB_STRINGS_DIR, name)))
    merged.update(_load_json(OVERRIDES))
    # 原文と同じ値の項目は無意味。ただし "⚠ {0}" のようなテンプレートは、取り込んだ部分を
    # 別途翻訳させるために残す。
    return {en: ja for en, ja in merged.items()
            if isinstance(en, str) and isinstance(ja, str) and ja and en not in PROTECTED
            and (en != ja or "{" in en)}


def _script_json(obj):
    """インライン <script> の中に置いても安全な JSON。"""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (s.replace("</", "<\\/").replace("<!--", "<\\!--")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def build_tag():
    """辞書と翻訳スクリプトを載せた <script> 要素（1 回だけ作る）。"""
    global _tag
    if _tag is None:
        with open(JS_PATH, encoding="utf-8") as f:
            js = f.read().replace("</script", "<\\/script")
        text = ('<script id="fizgig-ja">window.__JA_CAT=' + _script_json({"m": load_catalog()}) + ";\n"
                + js + "\n</script>\n")
        _tag = text.encode("utf-8")
    return _tag


def inject(page):
    """</body> の前に翻訳スクリプトを足したページ（bytes → bytes）。"""
    tag = build_tag()
    i = page.rfind(b"</body>")
    return page[:i] + tag + page[i:] if i >= 0 else page + tag


def apply(server_module):
    """fizgig.web.server のリクエストハンドラへフックを掛ける。ハンドラの形が変わっていたら例外を
    投げる（呼び出し側が記録し、ページは英語のままになる）。"""
    handler = getattr(server_module, "Handler", None)
    send = getattr(handler, "_send", None)
    if send is None:
        raise RuntimeError("fizgig.web.server.Handler._send not found (Fizgig changed its web server)")
    if getattr(send, "_ja_hooked", False):
        return

    def _send(self, code, body, ctype, extra=()):
        try:
            if (code == 200 and isinstance(body, (bytes, bytearray)) and str(ctype).startswith("text/html")
                    and PAGE_MARK in body):
                body = inject(bytes(body))
        except Exception:
            log_error("web.inject")
        return send(self, code, body, ctype, extra)

    _send._ja_hooked = True
    handler._send = _send
