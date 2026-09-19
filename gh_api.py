#!/usr/bin/env python3
"""Fetch GitHub API endpoints for geo-grounding. Reads token from /workspace/.gh_token.env."""
import sys, json, urllib.request

TOKFILE = "/workspace/.gh_token.env"
def get_token():
    with open(TOKFILE) as f:
        t = f.read().strip()
    if "=" in t:
        t = t.split("=", 1)[1].strip()
    return t

def api(path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {get_token()}",
        "User-Agent": "hermes-contributor",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prs":
        st, d = api("/repos/Baboratory/geo-grounding/pulls?state=open&per_page=100")
        prs = [p for p in d if "number" in p]
        print(f"TOTAL_OPEN={len(prs)}")
        for p in sorted(prs, key=lambda x: x["number"]):
            print(f"#{p['number']} | {p['title'][:55]} | {p['head']['ref']} | mergeable={p.get('mergeable')} | comments={p.get('comments')} | reviews={p.get('review_comments')}")
    elif cmd == "files":
        prnum = sys.argv[2]
        st, d = api(f"/repos/Baboratory/geo-grounding/pulls/{prnum}/files?per_page=100")
        if isinstance(d, dict):
            print("ERROR", st, d.get("message"))
        else:
            for f in d:
                print(f["filename"], f.get("status"))
    elif cmd == "get":
        path = sys.argv[2]
        st, d = api(path)
        print("STATUS", st)
        print(json.dumps(d)[:12000])
    elif cmd == "status":
        prnum = sys.argv[2]
        st, d = api(f"/repos/Baboratory/geo-grounding/pulls/{prnum}")
        print("STATUS", st)
        print("mergeable=", d.get("mergeable"))
        print("mergeable_state=", d.get("mergeable_state"))
        print("state=", d.get("state"))
        print("head_sha=", d.get("head", {}).get("sha"))
        print("changed_files=", d.get("changed_files"))
        print("additions=", d.get("additions"), "deletions=", d.get("deletions"))
    elif cmd == "post":
        path, payload = sys.argv[2], json.loads(sys.argv[3])
        st, d = api(path, "POST", payload)
        print("STATUS", st)
        print(json.dumps(d)[:2000])