import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
pr = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls/52')
print("mergeable:", pr.get('mergeable'), "| state:", pr.get('mergeable_state'))
cr = gh(f"https://api.github.com/repos/Baboratory/geo-grounding/commits/{pr['head']['sha']}/check-runs?per_page=100")
for c in cr.get('check_runs', []):
    print("check:", c['name'], '->', c['conclusion'])