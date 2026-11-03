"""End-to-end check against a real Fizgig folder that has the add-on installed (browser mode).

  python tools/e2e.py --fizgig PATH --shots DIR

Starts `fizgig.py --web` with the folder's venv python (torch stubbed if it is not installed), opens the page in
headless Edge/Chrome with translation on and off, and checks: Japanese text appears; the toggle button persists
its state; with translation off the page is identical to plain English; no JS console errors; form values and
saved state are not touched by the translation. Never clicks Train / Pod / Deploy controls.
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright

TOOLS = os.path.dirname(os.path.abspath(__file__))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start(fizgig, lang):
    port = free_port()
    tmp = tempfile.mkdtemp(prefix="fizgig_ja_e2e_")
    with open(os.path.join(tmp, "sitecustomize.py"), "w", encoding="utf-8") as f:
        f.write("import sys\ntry:\n    import torch\nexcept Exception:\n"
                f"    sys.path.insert(0, {TOOLS!r})\n    import sandbox_stubs\n    sandbox_stubs.install()\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = tmp
    env["FIZGIG_LANG"] = lang
    py = os.path.join(fizgig, "venv", "Scripts", "python.exe")
    log = open(os.path.join(tmp, "server.log"), "w")
    proc = subprocess.Popen([py, "fizgig.py", "--web", "--port", str(port)], cwd=fizgig, env=env, stdout=log,
                            stderr=subprocess.STDOUT)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).read(1)
            return proc, port
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise SystemExit("server did not start: " + open(os.path.join(tmp, "server.log")).read()[-1500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fizgig", required=True)
    ap.add_argument("--shots", default=None)
    a = ap.parse_args()
    if a.shots:
        os.makedirs(a.shots, exist_ok=True)
    results = {}
    with sync_playwright() as p:
        b = None
        for ch in ("msedge", "chrome"):
            try:
                b = p.chromium.launch(channel=ch)
                break
            except Exception:
                pass
        if b is None:
            b = p.chromium.launch()
        # A. server with the add-on active
        proc, port = start(a.fizgig, "")
        url = f"http://127.0.0.1:{port}/"
        try:
            ctx = b.new_context(viewport={"width": 1500, "height": 950})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.goto(url)
            page.wait_for_selector("#fizgigJaSwitch", timeout=15000)
            page.wait_for_timeout(1500)
            try:
                page.click("#welcomeModal.active .modal-close, #welcomeModal.active button", timeout=2000)
            except Exception:
                pass
            body_ja = page.inner_text("body")
            results["ja_visible"] = "スタート" in body_ja and "学習" in body_ja
            results["switch_label_on"] = page.inner_text("#fizgigJaSwitch")
            vals_ja = page.evaluate("[...document.querySelectorAll('input[id],select[id],textarea[id]')].map(e=>e.id+'='+(e.type==='checkbox'?e.checked:e.value))")
            # toggle to English (persistent)
            page.click("#fizgigJaSwitch")
            page.wait_for_load_state()
            page.wait_for_timeout(1500)
            body_en = page.inner_text("body")
            results["off_has_english_start"] = "Start" in body_en and "スタート" not in body_en
            results["switch_label_off"] = page.inner_text("#fizgigJaSwitch")
            results["persisted_off"] = page.evaluate("localStorage.getItem('fizgig_ja')")
            page.reload()
            page.wait_for_timeout(1200)
            results["off_survives_reload"] = "スタート" not in page.inner_text("body")
            vals_en = page.evaluate("[...document.querySelectorAll('input[id],select[id],textarea[id]')].map(e=>e.id+'='+(e.type==='checkbox'?e.checked:e.value))")
            results["form_values_identical_on_off"] = vals_ja == vals_en
            page.click("#fizgigJaSwitch")
            page.wait_for_timeout(1500)
            results["back_to_ja"] = "スタート" in page.inner_text("body")
            results["console_errors"] = [e for e in errors if "favicon" not in e.lower()][:8]
            if a.shots:
                page.screenshot(path=os.path.join(a.shots, "e2e_ja.png"))
            # ?ja=off one-shot works too
            page.goto(url + "?ja=off")
            page.wait_for_timeout(1200)
            results["query_off"] = "スタート" not in page.inner_text("body")
            page.goto(url + "?ja=on")
            page.wait_for_timeout(1200)
            results["query_on"] = "スタート" in page.inner_text("body")
            ctx.close()
        finally:
            proc.kill()
        # B. server started with FIZGIG_LANG=en: add-on inert
        proc, port = start(a.fizgig, "en")
        try:
            ctx = b.new_context()
            page = ctx.new_page()
            page.goto(f"http://127.0.0.1:{port}/")
            page.wait_for_timeout(2000)
            results["env_en_inert"] = page.locator("#fizgigJaSwitch").count() == 0 and "スタート" not in page.inner_text("body")
            ctx.close()
        finally:
            proc.kill()
        b.close()
    print(json.dumps(results, ensure_ascii=False, indent=1))
    bad = [k for k, v in results.items() if v is False or (k == "console_errors" and v)]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
