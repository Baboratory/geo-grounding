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

for i in range(8):
    d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53")
    files = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53/files")
    names = [f['filename'] for f in files]
    rus = [n for n in names if 'RUS' in n or 'UKR' in n or n=='data/languages/sah.yaml']
    print(f"poll {i}: mergeable={d.get('mergeable')} state={d.get('mergeable_state')} files={len(names)} stale_rusukr={rus}")
    if d.get('mergeable') is not None and not rus:
        print("CLEAN: PR#53 now clean and mergeable.")
        break
    time.sleep(8)