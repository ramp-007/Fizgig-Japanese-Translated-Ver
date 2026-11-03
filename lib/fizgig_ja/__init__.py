"""Fizgig 日本語化アドオン — ブートストラップ。

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors):
the Tk (Gizmo / Fizgig 7) layer was dropped, the package was renamed and the rest adapted for Japanese.

venv の site-packages にある ``fizgig_ja.pth`` の 1 行が、Python 起動時にこのパッケージを import します。
ここでは何も変更せず、``fizgig.web.server`` が import される瞬間にだけ翻訳フックを仕掛けます。
学習サブプロセスなど、そのモジュールを使わないプロセスには何の影響もありません。

無効にするには環境変数 ``FIZGIG_LANG=en`` を設定してください。
"""
import importlib.util
import os
import sys

__version__ = "1.0.0"
#: 辞書を作ったときの Fizgig（これより新しい版でも動く。新しい文言だけが英語で表示される）
__fizgig_baseline__ = "2026-11-02 main"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TARGET = "fizgig.web.server"


def _patch_web(module):
    from . import web
    try:
        web.apply(module)
    except Exception:
        web.log_error("web.apply")


class _WebFinder:
    """本物の fizgig.web.server を import させ、実行済みのモジュールにフックを掛ける。"""

    def find_spec(self, fullname, path=None, target=None):
        if fullname != _TARGET:
            return None
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass
        try:
            spec = importlib.util.find_spec(fullname)
        except Exception:
            return None
        if spec is None or spec.loader is None or not hasattr(spec.loader, "exec_module"):
            return spec
        loader = spec.loader
        orig_exec = loader.exec_module

        def exec_module(module):
            orig_exec(module)
            _patch_web(module)

        try:
            loader.exec_module = exec_module
        except Exception:
            return None
        return spec


def install():
    if os.environ.get("FIZGIG_LANG", "").lower().startswith("en"):
        return
    if _TARGET in sys.modules:
        _patch_web(sys.modules[_TARGET])
    elif not any(isinstance(f, _WebFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _WebFinder())


try:
    install()
except Exception:
    try:
        from . import web as _w
        _w.log_error("install")
    except Exception:
        pass
