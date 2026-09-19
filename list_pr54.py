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

files = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/54/files")
print("=== PR #54 files (%d) ===" % len(files))
for f in files:
    print("  ", f['filename'])
# wait for mergeable_state to settle
for i in range(6):
    d = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/54")
    ms = d.get('mergeable_state')
    print(f"poll state={ms} mergeable={d.get('mergeable')}")
    if ms == 'clean':
        break
    time.sleep(5)