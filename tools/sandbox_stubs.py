"""Stubs for importing Fizgig's web server/schema in environments without heavy packages such as torch (CI, cloud sandboxes).

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).

The goal is to extract translatable strings and check the screens, not to run training. If a real package is
installed it is used; only the missing ones are replaced with MagicMock modules. On the user's PC (the real
Fizgig venv) this does nothing.
"""
import importlib.abc
import importlib.machinery
import sys
import types
from unittest.mock import MagicMock

HEAVY = {"torch", "torchvision", "torchaudio", "bitsandbytes", "accelerate", "diffusers", "transformers",
         "tokenizers", "sentencepiece", "einops", "hqq", "comfy_kitchen", "triton", "cv2", "scipy",
         "huggingface_hub", "soundfile", "librosa", "av", "onnxruntime", "insightface", "pynvml", "webview"}


class _Mod(types.ModuleType):
    __path__ = []

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        v = MagicMock(name=f"{self.__name__}.{name}")
        setattr(self, name, v)
        return v


class _Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] not in HEAVY:
            return None
        for f in sys.meta_path:                      # a real installed package wins
            if f is self or not hasattr(f, "find_spec"):
                continue
            try:
                if f.find_spec(name, path, target) is not None:
                    return None
            except Exception:
                continue
        return importlib.machinery.ModuleSpec(name, self, is_package=True)

    def create_module(self, spec):
        return _Mod(spec.name)

    def exec_module(self, module):
        pass


def install():
    if not any(isinstance(f, _Finder) for f in sys.meta_path):
        sys.meta_path.append(_Finder())
