import json, urllib.request, urllib.error
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def opener(url, depth=0):
    req = urllib.request.Request(url, headers={'Authorization':'Bearer '+tok})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, r.read().decode('utf-8','replace'), r.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (301,302,303,307) and depth < 12:
            return opener(e.headers.get('Location'), depth+1)
        return e.code, None, None
jobs = json.load(urllib.request.urlopen(urllib.request.Request(
    'https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/35499081504/jobs',
    headers={'Authorization':'Bearer '+tok})))
for j in jobs.get('jobs', []):
    print("job", j['id'], j['conclusion'], 'logs_url=', j['logs_url'])
    st, content, final = opener(j['logs_url'])
    print("status:", st, "final url host:", final)
    if content:
        print("LEN", len(content))
        print(content[-4000:])