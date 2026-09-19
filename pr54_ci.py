import json, urllib.request

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

# combined status
try:
    st = gh("https://api.github.com/repos/Baboratory/geo-grounding/commits/7567dd8c3c803cb54a7f2e49140252b781973777/status")
    print("== combined status ==")
    print("state:", st.get('state'))
    for s in st.get('statuses', []):
        print("  **", s.get('state'), "|", s.get('context'), "|", (s.get('description') or '')[:80])
except Exception as e:
    print("status err", e)

# check runs
try:
    runs = gh("https://api.github.com/repos/Baboratory/geo-grounding/commits/7567dd8c3c803cb54a7f2e49140252b781973777/check-runs")
    print("== check runs ==")
    for r in runs.get('check_runs', []):
        print("  ", r.get('status'), r.get('conclusion'), "|", r.get('name'))
except Exception as e:
    print("checkrun err", e)