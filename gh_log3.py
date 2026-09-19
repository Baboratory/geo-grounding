import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
url='https://api.github.com/repos/Baboratory/geo-grounding/actions/jobs/106047462251/logs'
req = urllib.request.Request(url, headers={'Authorization':'Bearer '+tok})
try:
    r = urllib.request.urlopen(req, timeout=60)
    print("ok", r.status)
except urllib.error.HTTPError as e:
    print("code", e.code)
    print("Location:", e.headers.get('Location'))
    print("headers:", dict(e.headers))