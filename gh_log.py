import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
url='https://api.github.com/repos/Baboratory/geo-grounding/actions/jobs/106047462251/logs'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}'})
try:
    data = urllib.request.urlopen(req).read().decode('utf-8','replace')
    print(data[-3000:])
except Exception as e:
    print("err", repr(e), e.read() if hasattr(e,'read') else '')
    import http.client
    print(getattr(e,'headers',None))