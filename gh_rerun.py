import json, urllib.request, urllib.error
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
url='https://api.github.com/repos/Baboratory/geo-grounding/actions/runs/35499081504/rerun-failed-jobs'
req = urllib.request.Request(url, data=b'{}', method='POST',
    headers={'Authorization':'Bearer '+tok, 'Content-Type':'application/json',
             'Accept':'application/vnd.github+json'})
try:
    r = urllib.request.urlopen(req, timeout=60)
    print("rerun requested:", r.status)
except urllib.error.HTTPError as e:
    print("ERR", e.code, e.read().decode()[:400])