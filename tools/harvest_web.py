"""Drive the Fizgig 8+ web UI in a headless browser to collect/check on-screen strings.

Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).

  python tools/harvest_web.py [--fizgig PATH]            collect English strings  -> work/web_runtime.json
  python tools/harvest_web.py [--fizgig PATH] --check    check leftover English after translation (exit code 1 if any remain)
  Options: --shots DIR   save per-tab screenshots,  --no-copy  run in the Fizgig folder as-is without copying it

What it does: copies the Fizgig folder to a temporary location and starts the server (no training is run; if torch
is missing, sandbox_stubs substitutes for it), then clicks through every model family x tab x training type x sub-tab
and collects the DOM text nodes and the title/placeholder/alt/aria-label attributes. Strings in hidden panels are
also caught if they are in the DOM.
--check does the same traversal with the translator (fizgig_ja) enabled and reports the strings the translator
could not replace (window.__ja.missing()).

Requires: pip install playwright (+ Chromium: in the sandbox it is at /opt/pw-browsers)
"""
import argparse
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT_DIR, "work")
TOOLS = os.path.dirname(os.path.abspath(__file__))

SNAPSHOT_JS = r"""
() => {
  const out = {text: [], attr: []};
  const skip = (e) => { for (; e && e.nodeType === 1; e = e.parentElement) {
      const t = e.tagName;
      if (t === 'SCRIPT' || t === 'STYLE' || t === 'NOSCRIPT' || t === 'TEXTAREA' || t === 'PRE' || t === 'TEMPLATE') return true;
      if (e.getAttribute('translate') === 'no') return true; } return false; };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) { if (!skip(n.parentElement) && n.nodeValue && n.nodeValue.trim()) out.text.push(n.nodeValue); }
  for (const e of document.querySelectorAll('*')) {
    if (skip(e)) continue;
    for (const a of ['title', 'placeholder', 'alt', 'aria-label', 'label']) {
      const v = e.getAttribute(a); if (v && v.trim()) out.attr.push(v);
    }
  }
  return out;
}
"""


#: every control that has an id, with what the app would read from it (value / checked / each option's value)
VALUES_JS = r"""
() => {
  const o = {};
  for (const e of document.querySelectorAll('input[id],select[id],textarea[id]')) {
    if (e.type === 'checkbox' || e.type === 'radio') o[e.id] = String(e.checked);
    else if (e.tagName === 'SELECT') o[e.id] = e.value + ' | ' + [...e.options].map(x => x.value).join(',');
    else o[e.id] = e.value;
  }
  return o;
}
"""


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _chromium(p):
    for ch in ("msedge", "chrome"):
        try:
            return p.chromium.launch(channel=ch)
        except Exception:
            pass
    try:
        return p.chromium.launch(args=["--no-sandbox"])
    except Exception:
        for path in sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome")):
            return p.chromium.launch(executable_path=path, args=["--no-sandbox"])
        raise


def _start_server(root, with_ja):
    port = _free_port()
    tmp = tempfile.mkdtemp(prefix="fizgig_ja_harvest_")
    lines = ["import sys"]
    lines.append("try:\n    import torch  # noqa\nexcept Exception:\n"
                 f"    sys.path.insert(0, {TOOLS!r})\n    import sandbox_stubs\n    sandbox_stubs.install()")
    if with_ja:
        lines.append(f"sys.path.insert(0, {os.path.join(ROOT_DIR, 'lib')!r})\nimport fizgig_ja")
    with open(os.path.join(tmp, "sitecustomize.py"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = tmp + os.pathsep + env.get("PYTHONPATH", "")
    # English for a plain harvest (a .pth in the venv would otherwise translate what we are collecting);
    # --check turns the translator on and is told what it could not translate
    if with_ja:
        env.pop("FIZGIG_LANG", None)
    else:
        env["FIZGIG_LANG"] = "en"
    log = open(os.path.join(tmp, "server.log"), "w")
    proc = subprocess.Popen([sys.executable, "fizgig.py", "--web", "--port", str(port)], cwd=root, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read(1)
            return proc, port, tmp
        except Exception:
            if proc.poll() is not None:
                break
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("The server did not start:\n" + open(os.path.join(tmp, "server.log")).read()[-1500:])


def _settle(page, ms=450):
    page.wait_for_timeout(ms)


def walk_ui(page, snap, shots=None, after_family=None):
    """Visit every family, tab, training kind and sub-tab, calling snap(label) after each."""
    page.set_default_timeout(4000)
    # the welcome tour opens once the app has booted; it covers the page until it is closed
    try:
        page.wait_for_selector("#welcomeModal.active", timeout=10000)
        _settle(page, 600)
        snap("welcome")
        page.click("#welcomeClose")
        page.wait_for_selector("#welcomeModal.active", state="detached", timeout=3000)
    except Exception:
        pass
    _settle(page, 500)
    families = page.evaluate("() => { const s = document.querySelector('.family-pick'); "
                             "return s ? [...s.options].map(o => o.value) : []; }")
    print("  families", len(families), families, flush=True)
    tabs = page.eval_on_selector_all("button.tab-item", "els => els.map(e => e.dataset.tab)")
    print("  tabs", len(tabs), flush=True)

    def shot(name):
        if shots:
            os.makedirs(shots, exist_ok=True)
            page.screenshot(path=os.path.join(shots, re.sub(r"[^\w.-]+", "_", name) + ".png"), full_page=False)

    for fam in families or [None]:
        print("  >", fam, flush=True)
        if fam:
            try:
                # the pick sits on the Start tab (hidden elsewhere): set it and fire its change event
                page.evaluate("""(v) => { const s = document.querySelector('.family-pick'); s.value = v;
                                          s.dispatchEvent(new Event('change', {bubbles: true})); }""", fam)
                _settle(page, 1200)
            except Exception as e:
                print("  family switch failed", fam, str(e)[:60])
                continue
        for t in tabs:
            try:
                page.click(f'button.tab-item[data-tab="{t}"]')
                _settle(page)
            except Exception:
                continue
            snap(f"{fam}/{t}")
            if fam == families[0] if families else True:
                shot(f"{t}")
            # sub-tabs / sub-modes of a tab
            for sel in ("#tab-%s .ry-tab" % t, "#tab-%s [data-exmode]" % t, "#tab-%s [data-mode]" % t):
                try:
                    for i in range(page.locator(sel).count()):
                        page.locator(sel).nth(i).click(timeout=1000)
                        _settle(page, 250)
                        snap(f"{fam}/{t}/sub{i}")
                except Exception:
                    pass
            if t == "training":
                # the "Kind of training" choice: found by its option values (their text is Korean once translated)
                kind = page.locator("#tab-training select:has(option[value^='Slider'])")
                try:
                    n = kind.first.locator("option").count()
                    for i in range(n):
                        kind.first.select_option(index=i)
                        _settle(page, 500)
                        snap(f"{fam}/training/kind{i}")
                        if fam == (families[0] if families else None):
                            shot(f"training_kind{i}")
                except Exception:
                    pass
        if after_family:
            after_family(fam)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fizgig", default=os.path.dirname(ROOT_DIR))
    ap.add_argument("--check", action="store_true", help="enable translation and check leftover English")
    ap.add_argument("--shots")
    ap.add_argument("--no-copy", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--values", help="also write {tab: {element id: value}} (form values, select options) to this file")
    args = ap.parse_args()
    root = os.path.abspath(args.fizgig)
    if not os.path.isfile(os.path.join(root, "src", "fizgig", "web", "static", "index.html")):
        raise SystemExit("This is not a Fizgig 8+ folder.")
    work_root = root
    tmp_copy = None
    if not args.no_copy:
        tmp_copy = tempfile.mkdtemp(prefix="fizgig_copy_")
        work_root = os.path.join(tmp_copy, "fizgig")
        shutil.copytree(root, work_root, ignore=shutil.ignore_patterns(".git", "venv", "ja", "user_data", "__pycache__",
                                                                       "*.mp4", "models", "node_modules"))
    from playwright.sync_api import sync_playwright
    proc, port, tmp = _start_server(work_root, args.check)
    result = {"text": {}, "attr": {}, "missing": {}}
    values = {}
    out_path = args.out or os.path.join(WORK, "web_missing_runtime.json" if args.check else "web_runtime.json")
    try:
        with sync_playwright() as p:
            b = _chromium(p)
            ctx = b.new_context(viewport={"width": 1500, "height": 950})
            if args.check:
                ctx.add_init_script("window.__JA_COLLECT = true")
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{port}/", wait_until="load")
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))

            def snap(label):
                if args.values:
                    values[label] = page.evaluate(VALUES_JS)
                s = page.evaluate(SNAPSHOT_JS)
                for t in s["text"]:
                    result["text"].setdefault(t, set()).add(label.split("/")[1] if "/" in label else label)
                for a in s["attr"]:
                    result["attr"].setdefault(a, set()).add(label.split("/")[1] if "/" in label else label)
                if args.check:
                    for k, n in page.evaluate("window.__ja ? __ja.missing() : []"):
                        result["missing"].setdefault(k, set()).add(label)

            def flush(_fam=None):
                ser = {k: {s: sorted(v) for s, v in d.items()} for k, d in result.items()}
                os.makedirs(WORK, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(ser, f, ensure_ascii=False, indent=1)

            walk_ui(page, snap, args.shots, after_family=flush)
            if args.values:
                with open(args.values, "w", encoding="utf-8") as f:
                    json.dump(values, f, ensure_ascii=False, indent=1, sort_keys=True)
            b.close()
            if errors:
                print("Page errors:", errors[:3])
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)
        if tmp_copy:
            shutil.rmtree(tmp_copy, ignore_errors=True)

    ser = {k: {s: sorted(v) for s, v in d.items()} for k, d in result.items()}
    os.makedirs(WORK, exist_ok=True)
    out = out_path
    with open(out, "w", encoding="utf-8") as f:
        json.dump(ser, f, ensure_ascii=False, indent=1)
    if args.check:
        left = {k: v for k, v in ser["missing"].items() if _worth_reporting(k)}
        print(f"English the translator could not replace: {len(left)} -> {out}")
        return 1 if left else 0
    print(f"Collected: {len(ser['text'])} texts, {len(ser['attr'])} attributes -> {out}")
    return 0


def _worth_reporting(s):
    """False for what is English on purpose: already Japanese around a name, or in tools/web_keep_english.json."""
    if not re.search(r"[A-Za-z]{3}", s) or re.search(r"[\uac00-\ud7a3]", s):
        return False
    sys.path.insert(0, TOOLS)
    from extract_web import _keep_english
    keep = _worth_reporting.__dict__.setdefault("keep", _keep_english())
    core = re.sub(r"\s*[:*]+\s*$", "", s.strip())
    return not (keep(s.strip()) or keep(core) or keep(core.strip(" :*")))


if __name__ == "__main__":
    sys.exit(main())
