import json, urllib.request

def get_token():
    with open('/workspace/.gh_token.env') as f:
        for line in f:
            if '=' in line:
                return line.split('=',1)[1].strip()
    return None

tok = get_token()
def gh(url, method='GET', data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method=method, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'curl/8', 'Content-Type':'application/json'}, data=body)
    return json.load(urllib.request.urlopen(req))

# Close PR #53 (stale head from branch delete/recreate)
closed = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53", method='PATCH', data={"state":"closed"})
print("closed #53:", closed.get('state'))

# Reopen a clean PR against the same (now-clean) branch
body = """Adds **Saudi Arabia (SAU)**, the **United Arab Emirates (ARE)** and **Yemen (YEM)** — the Arabian Peninsula.

**Governance classification** (per DESIGN.md 2-of-3 test, ISO 3166-2 verified via pycountry):
- **SAU** — `unitary-large` (~36M); curated Riyadh (SA-01), Makkah (SA-02) and Eastern Province (SA-04) + WHOLE fallback.
- **ARE** — `federal` (seven constitutional emirates); curated Abu Dhabi (AE-AZ), Dubai (AE-DU) and Sharjah (AE-SH) + WHOLE.
- **YEM** — `unitary-large` (~34M); curated Sana'a (YE-SN), Aden (YE-AD) and Hadramawt (YE-HD) + WHOLE.

**New language files:** `ara` (Arabic) and `hin` (Hindi), both verified active on iso639-3.sil.org.

**Quality gate (all green):** `scripts/validate.py` 0 errors; `yamllint -c .yamllint.yaml` clean (incl. new-line-at-end-of-file, never filtered); `codespell data/` clean; `pytest tests/` 28 passed. Trailing newline verified on every committed blob.

Includes the standard `[tool.setuptools] packages=[]` fix so the editable CI install is deterministic.
"""
pr = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls", method='POST', data={
    "title": "Add Saudi Arabia (SAU), the UAE (ARE) and Yemen (YEM) — Arabian Peninsula",
    "head": "devContributor:batch-53/add-sau-are-yem",
    "base": "main",
    "body": body,
})
print("NEW PR number:", pr.get('number'))
print("url:", pr.get('html_url'))
print("head sha:", pr.get('head',{}).get('sha'))