import json, urllib.request, time

def get_token():
    with open('/workspace/.gh_token.env') as f:
        for line in f:
            if '=' in line:
                return line.split('=',1)[1].strip()
    return None

tok = get_token()
def gh(url, method='GET'):
    req = urllib.request.Request(url, method=method, headers={'Authorization': f'Bearer {tok}', 'User-Agent':'curl/8'})
    return json.load(urllib.request.urlopen(req))

# poll mergeable until settled
for i in range(6):
    d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53")
    if d.get('mergeable') is not None:
        break
    time.sleep(3)
print("mergeable:", d.get('mergeable'), "| state:", d.get('mergeable_state'))
print("title:", d['title'])
files = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/53/files")
print("files in PR:", len(files))
for f in files:
    print("  ", f['filename'], "+%d" % f['additions'] if f['additions'] else "")
# check for any non-data, non-pyproject files
bad = [f['filename'] for f in files if not (f['filename'].endswith('.yaml') or f['filename']=='pyproject.toml')]
print("stray files:", bad if bad else "(none)")