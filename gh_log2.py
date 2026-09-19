import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
url='https://api.github.com/repos/Baboratory/geo-grounding/actions/jobs/106047462251/logs'

def fetch(url, headers, depth=0):
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return resp.status, resp.read().decode('utf-8','replace')
    except urllib.error.HTTPError as e:
        if e.code in (301,302,303,307,308) and depth < 10:
            loc = e.headers.get('Location')
            if loc.startswith('http'):
                return fetch(loc, headers, depth+1)
            else:
                from urllib.parse import urljoin
                return fetch(urljoin(url, loc), headers, depth+1)
        # retry once with basic header if 401
        if e.code == 401 and depth < 3:
            return fetch(url, {'Authorization':'Bearer '+tok}, depth+1)
        return e.code, str(e)

st, content = fetch(url, {'Authorization':'Bearer '+tok})
print("status:", st, "len:", len(content))
print(content[-3000:])