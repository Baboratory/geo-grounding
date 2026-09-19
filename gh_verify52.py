import json, urllib.request, time
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
time.sleep(5)
pr = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls/52')
print("mergeable:", pr.get('mergeable'), "| state:", pr.get('mergeable_state'))
# check statuses/checks
try:
    statuses = gh('https://api.github.com/repos/Baboratory/geo-grounding/commits/'+pr['head']['sha']+'/check-runs?per_page=100')
    for c in statuses.get('check_runs', []):
        print("check:", c['name'], '->', c['status'], c['conclusion'])
except Exception as e:
    print("checks err", e)