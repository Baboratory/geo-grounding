import json, urllib.request
tok = [l for l in open('/workspace/.gh_token.env') if '=' in l][0].split('=',1)[1].strip()
def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {tok}', 'Accept':'application/vnd.github+json'})
    return json.load(urllib.request.urlopen(req))
pr = gh('https://api.github.com/repos/Baboratory/geo-grounding/pulls/52')
sha = pr['head']['sha']
cr = gh(f'https://api.github.com/repos/Baboratory/geo-grounding/commits/{sha}/check-runs?per_page=100')
for c in cr.get('check_runs', []):
    print("name:", c['name'], '| status:', c['status'], '| concl:', c['conclusion'], '| details:', c.get('details_url'))
    if c.get('output', {}).get('text'):
        print("OUTPUT TEXT:", c['output']['text'][:2000])
    for a in c.get('output', {}).get('annotations', [])[:20]:
        print("  ANN:", a.get('path'), a.get('start_line'), '-', a.get('message'))