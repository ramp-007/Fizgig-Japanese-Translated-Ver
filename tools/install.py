"""Fizgig 日本語化アドオンの導入 / 削除。

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).

  <Fizgig の venv の python> tools/install.py            導入（何度実行しても安全）
  <Fizgig の venv の python> tools/install.py --remove   削除
  <Fizgig の venv の python> tools/install.py --status   導入状態の確認

やること
  1. venv の site-packages に fizgig_ja.pth を 1 つ置く。Python 起動時にこのフォルダの lib を
     sys.path に足して fizgig_ja を import する 1 行。fizgig_ja は fizgig.web.server が import
     された瞬間にだけ翻訳フックを掛ける。venv は git の管理外なので git pull / update_fizgig で消えない。
  2. Fizgig リポジトリの .git/info/exclude に、このフォルダ名を追加する（git status を汚さない）。
     .gitignore は Fizgig 本体のファイルなので触らない。
"""
import os
import subprocess
import sys
import sysconfig

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIZGIG_DIR = os.path.dirname(ADDON_DIR)
LIB = os.path.join(ADDON_DIR, "lib")
PTH_NAME = "fizgig_ja.pth"


def site_packages():
    # この venv の python が実行するので、purelib がそのまま venv の site-packages になる
    return sysconfig.get_paths()["purelib"]


def pth_line():
    # site.py は import で始まる行を exec する。まず venv からの相対位置を探し（フォルダごと移動しても動く）、
    # 無ければ記録した絶対パスを使う。
    return ("import sys, os; _p = os.path.join(os.path.dirname(sys.prefix), %r, 'lib'); "
            "_p = _p if os.path.isdir(_p) else %r; "
            "(_p in sys.path) or sys.path.append(_p); "
            "__import__('fizgig_ja') if os.path.isdir(_p) else None\n"
            % (os.path.basename(ADDON_DIR), LIB))


def hook_registered():
    """新しい Python を起動して、フックが待機しているか確認する（サーバー本体は torch を読むので import しない）。"""
    code = ("import sys, fizgig_ja; "
            "sys.exit(0 if any(type(f).__name__ == '_WebFinder' for f in sys.meta_path) else 1)")
    env = dict(os.environ)
    env.pop("FIZGIG_LANG", None)
    return subprocess.run([sys.executable, "-c", code], env=env).returncode == 0


def install():
    sp = site_packages()
    rel = os.path.join(os.path.dirname(os.path.abspath(sys.prefix)), os.path.basename(ADDON_DIR), "lib")
    if os.path.normcase(os.path.abspath(rel)) != os.path.normcase(os.path.abspath(LIB)):
        print("[お知らせ] このフォルダは Fizgig フォルダの直下にありません。絶対パスで導入するので今は動きますが、"
              "Fizgig フォルダやこのフォルダを移動したら、もう一度導入してください。")
    path = os.path.join(sp, PTH_NAME)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pth_line())
    print(f"[OK] {path}")

    exclude = os.path.join(FIZGIG_DIR, ".git", "info", "exclude")
    if os.path.isdir(os.path.join(FIZGIG_DIR, ".git")):
        os.makedirs(os.path.dirname(exclude), exist_ok=True)
        try:
            existing = open(exclude, encoding="utf-8").read() if os.path.exists(exclude) else ""
        except Exception:
            existing = ""
        entry = "/%s/" % os.path.basename(ADDON_DIR)
        if entry not in existing.splitlines():
            with open(exclude, "a", encoding="utf-8") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(entry + "\n")
            print(f"[OK] {exclude} に {entry} を追加しました")
        else:
            print(f"[OK] {exclude} には登録済みです")

    if hook_registered():
        print("[OK] 日本語化フックの登録を確認しました")
        return 0
    print("[失敗] フックが登録されませんでした。ja_error.log を確認してください。")
    return 1


def remove():
    path = os.path.join(site_packages(), PTH_NAME)
    if os.path.exists(path):
        os.remove(path)
        print(f"[OK] 削除しました: {path}")
    else:
        print("[OK] すでに削除されています。")
    return 0


def status():
    path = os.path.join(site_packages(), PTH_NAME)
    print("導入ファイル:", "あり" if os.path.exists(path) else "なし", path)
    if os.path.exists(path):
        print("フック:", "登録されています" if hook_registered() else "登録されていません")
    return 0


if __name__ == "__main__":
    if "--remove" in sys.argv:
        sys.exit(remove())
    sys.exit(status() if "--status" in sys.argv else install())
