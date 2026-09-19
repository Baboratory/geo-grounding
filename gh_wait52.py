import json, urllib.request, time
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
pr = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls/52')
sha = pr['head']['sha']
for i in range(10):
    try:
        cr = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/commits/{sha}/check-runs?per_page=100')
        runs = cr.get('check_runs', [])
        if runs and all(r['status']=='completed' for r in runs):
            for c in runs:
                print("check:", c['name'], '->', c['conclusion'])
            print("mergeable_state:", pr.get('mergeable_state'))
            break
    except Exception as e:
        print("err", e)
    time.sleep(15)
else:
    print("still running or no check info")