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

sha = "7567dd8c3c803cb54a7f2e49140252b781973777"
for i in range(10):
    d = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/pulls/54")
    runs = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/commits/{sha}/check-runs")
    concl = None
    for r in runs.get('check_runs', []):
        concl = f"{r.get('status')}/{r.get('conclusion')}"
    print(f"poll {i}: mergeable_state={d.get('mergeable_state')} validate={concl}")
    if d.get('mergeable_state') == 'clean' or (concl and 'completed' in concl):
        # re-read final
        d2 = gh("https://api.github.com/repos/Baboratory/geo-grounding/pulls/54")
        print("FINAL mergeable_state:", d2.get('mergeable_state'), "mergeable:", d2.get('mergeable'))
        break
    time.sleep(10)