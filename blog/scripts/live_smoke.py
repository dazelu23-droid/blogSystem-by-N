"""Hit a running blog server and verify theme/font dropdown assets."""
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"


def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def main():
    checks = []
    pages = ["/", "/login", "/signup", "/search"]

    for path in pages:
        status, html = fetch(path)
        ok = (
            status == 200
            and 'id="theme-toggle"' in html
            and 'id="font-toggle"' in html
            and 'data-theme="ocean"' in html
            and 'data-font="mono"' in html
        )
        checks.append((path, status, ok))

    status, css = fetch("/static/style.css")
    checks.append((
        "/static/style.css",
        status,
        status == 200 and '[data-theme="midnight"]' in css and ".pref-menu" in css,
    ))

    status, js = fetch("/static/theme.js")
    checks.append((
        "/static/theme.js",
        status,
        status == 200 and "blog-font" in js and "applyFont" in js,
    ))

    print(f"LIVE SERVER SMOKE TEST ({BASE})")
    failed = False
    for path, status, ok in checks:
        label = "PASS" if ok else "FAIL"
        print(f"  {path}: HTTP {status} -> {label}")
        if not ok or status != 200:
            failed = True

    print("OVERALL:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
