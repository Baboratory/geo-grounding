import json, urllib.request, time

def get_token():
    with open('/workspace/.gh_token.env') as f:
        for line in f:
            if '=' in line:
                return line.split('=',1)[1].strip()
    return None

tok = get_token()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'curl/8'})
    return json.load(urllib.request.urlopen(req))

for i in range(6):
    d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/54")
    files = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/54/files")
    names = [f['filename'] for f in files]
    rus = [n for n in names if 'RUS' in n or 'UKR' in n or n=='data/languages/sah.yaml']
    stray = [n for n in names if not (n.endswith('.yaml') or n=='pyproject.toml')]
    print(f"poll {i}: mergeable={d.get('mergeable')} state={d.get('mergeable_state')} files={len(names)} rusukr={rus} stray={stray}")
    if d.get('mergeable') is not None and not rus and not stray:
        break
    time.sleep(8)