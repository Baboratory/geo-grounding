import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url, data=None, method=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={'Authorization': f'Bearer {tok}', 'Content-Type':'application/json',
                 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
payload = {
  "title": "Add Russia (RUS) and Ukraine (UKR) — region-aware Europe",
  "head": "devContributor:batch-52/add-rus-ukr",
  "base": "main",
  "body": "Adds Russia (RUS) and Ukraine (UKR), completing the final two Europe region-heavy countries.\n\n**Russia (RUS)** — federal, 83 ISO 3166-2 federal subjects spanning ~11 time zones and dozens of official minority languages. Curated regions: Moscow (RU-MOW) and Saint Petersburg (RU-SPE) federal cities; Republic of Tatarstan (RU-TA, a Tatar-majority republic with Tatar and Russian both official at the regional level); Sakha Republic (RU-SA, the subarctic Yakut-majority north-east).\n\n**Ukraine (UKR)** — unitary-large with real ISO 3166-2 oblasts. Curated regions: Kyiv city (UA-30), Lvivska (UA-46, Galician cultural capital), Odeska (UA-51, Black Sea port) and Kharkivska (UA-63) oblasts.\n\n**Two new language entries** verified active on iso639-3.sil.org: Tatar (tat) and Yakut/Sakha (sah).\n\nQuality gate: scripts/validate.py 0 errors; yamllint -c .yamllint.yaml clean; codespell data/ clean; python -m pytest tests/ 28 passed; every committed file ends with a trailing newline. 'Composite estimate' publisher used for derived figures."
}
try:
    r = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls', payload)
    print("PR created:", r['number'], r['html_url'])
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:600])