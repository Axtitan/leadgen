"""LeadFinder - finds local businesses with no website or a bad one, and tells you what to pitch.

    python app.py                    start the app            (http://127.0.0.1:8790)
    python app.py --port 9000        use another port
    python app.py --grade URL        check one website in the terminal and exit
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leadfinder import db  # noqa: E402


def grade_cli(url):
    from leadfinder import grader
    res = grader.grade(url)
    bucket, score, issues, headline = grader.finalize(res)
    print(f"\n{url}\n  {bucket.upper()}" + (f"  {score}/100" if score is not None else "") + f"  - {headline}\n")
    for i in issues:
        print(f"  -{i['pts']:>2}  {i['title']}\n        {i['pitch']}")
    s = res.get("site") or {}
    for k in ("final_url", "ms", "builder", "copyright_year", "emails", "socials"):
        if s.get(k):
            print(f"  {k}: {s[k]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--grade", metavar="URL")
    a = ap.parse_args()
    db.init()
    if a.grade:
        return grade_cli(a.grade)
    from leadfinder.engine import Engine
    from leadfinder.server import serve
    eng = Engine()
    eng.start()
    serve(a.host, a.port, eng)


if __name__ == "__main__":
    main()
